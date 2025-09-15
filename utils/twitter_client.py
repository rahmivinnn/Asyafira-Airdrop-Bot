import tweepy
import requests
import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urljoin, urlparse
import logging
from config.database import get_database
from utils.cookie_manager import CookieManager

class TwitterClient:
    """Advanced Twitter client for Asyafira Airdrop Bot"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = get_database()
        
        # Twitter API credentials
        self.api_key = config.get('TWITTER_API_KEY')
        self.api_secret = config.get('TWITTER_API_SECRET')
        self.access_token = config.get('TWITTER_ACCESS_TOKEN')
        self.access_token_secret = config.get('TWITTER_ACCESS_TOKEN_SECRET')
        self.bearer_token = config.get('TWITTER_BEARER_TOKEN')
        
        # Initialize Twitter API clients
        self.api_v1 = None
        self.api_v2 = None
        self.client = None
        
        # Cookie manager for web scraping
        self.cookie_manager = CookieManager(config)
        
        # Rate limiting
        self.rate_limits = {
            'tweets': {'count': 0, 'reset_time': 0, 'limit': int(config.get('TWITTER_RATE_LIMIT_TWEETS', 50))},
            'follows': {'count': 0, 'reset_time': 0, 'limit': int(config.get('TWITTER_RATE_LIMIT_FOLLOWS', 20))},
            'likes': {'count': 0, 'reset_time': 0, 'limit': int(config.get('TWITTER_RATE_LIMIT_LIKES', 100))},
            'retweets': {'count': 0, 'reset_time': 0, 'limit': int(config.get('TWITTER_RATE_LIMIT_RETWEETS', 30))}
        }
        
        # Action settings
        self.auto_tweet_success = config.get('AUTO_TWEET_SUCCESS', True)
        self.success_tweet_template = config.get('SUCCESS_TWEET_TEMPLATE', 
            '🎉 Successfully claimed airdrop with Asyafira Bot! #{hashtag} #airdrop #crypto')
        
        self.auto_follow_enabled = config.get('AUTO_FOLLOW_ENABLED', True)
        self.follow_accounts = [acc.strip() for acc in config.get('FOLLOW_ACCOUNTS', '').split(',') if acc.strip()]
        
        self.auto_retweet_enabled = config.get('AUTO_RETWEET_ENABLED', True)
        self.retweet_keywords = [kw.strip().lower() for kw in config.get('RETWEET_KEYWORDS', '').split(',') if kw.strip()]
        
        self.auto_like_enabled = config.get('AUTO_LIKE_ENABLED', True)
        self.like_keywords = [kw.strip().lower() for kw in config.get('LIKE_KEYWORDS', '').split(',') if kw.strip()]
        
        # Initialize API connections
        self._initialize_api()
    
    def _initialize_api(self) -> bool:
        """Initialize Twitter API connections"""
        try:
            if not all([self.api_key, self.api_secret, self.access_token, self.access_token_secret]):
                self.logger.warning("Twitter API credentials not fully configured")
                return False
            
            # Initialize API v1.1 (for legacy endpoints)
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_token_secret)
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Initialize API v2
            if self.bearer_token:
                self.client = tweepy.Client(
                    bearer_token=self.bearer_token,
                    consumer_key=self.api_key,
                    consumer_secret=self.api_secret,
                    access_token=self.access_token,
                    access_token_secret=self.access_token_secret,
                    wait_on_rate_limit=True
                )
            
            # Test connection
            if self.api_v1:
                user = self.api_v1.verify_credentials()
                self.logger.info(f"Twitter API initialized for user: @{user.screen_name}")
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Twitter API: {e}")
            return False
        
        return False
    
    def _check_rate_limit(self, action_type: str) -> bool:
        """Check if action is within rate limits"""
        current_time = time.time()
        rate_limit = self.rate_limits.get(action_type, {})
        
        # Reset counter if hour has passed
        if current_time > rate_limit.get('reset_time', 0):
            rate_limit['count'] = 0
            rate_limit['reset_time'] = current_time + 3600  # 1 hour
        
        # Check if within limit
        if rate_limit['count'] >= rate_limit.get('limit', 0):
            self.logger.warning(f"Rate limit reached for {action_type}")
            return False
        
        return True
    
    def _increment_rate_limit(self, action_type: str) -> None:
        """Increment rate limit counter"""
        if action_type in self.rate_limits:
            self.rate_limits[action_type]['count'] += 1
    
    def _add_random_delay(self, min_delay: int = 1, max_delay: int = 5) -> None:
        """Add random delay to avoid detection"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def tweet(self, text: str, media_paths: List[str] = None, reply_to: str = None) -> Optional[Dict]:
        """Post a tweet"""
        if not self._check_rate_limit('tweets'):
            return None
        
        try:
            media_ids = []
            
            # Upload media if provided
            if media_paths and self.api_v1:
                for media_path in media_paths:
                    try:
                        media = self.api_v1.media_upload(media_path)
                        media_ids.append(media.media_id)
                    except Exception as e:
                        self.logger.error(f"Failed to upload media {media_path}: {e}")
            
            # Post tweet
            if self.client:
                # Use API v2
                response = self.client.create_tweet(
                    text=text,
                    media_ids=media_ids if media_ids else None,
                    in_reply_to_tweet_id=reply_to
                )
                
                tweet_data = {
                    'id': response.data['id'],
                    'text': text,
                    'created_at': datetime.now().isoformat(),
                    'media_count': len(media_ids)
                }
                
            elif self.api_v1:
                # Use API v1.1
                status = self.api_v1.update_status(
                    status=text,
                    media_ids=media_ids if media_ids else None,
                    in_reply_to_status_id=reply_to
                )
                
                tweet_data = {
                    'id': str(status.id),
                    'text': text,
                    'created_at': status.created_at.isoformat(),
                    'media_count': len(media_ids)
                }
            
            else:
                self.logger.error("No Twitter API client available")
                return None
            
            # Log to database
            self.db.log_twitter_action(
                action_type='tweet',
                target_id=tweet_data['id'],
                content=text,
                status='success',
                response_data=tweet_data
            )
            
            self._increment_rate_limit('tweets')
            self._add_random_delay(2, 8)
            
            self.logger.info(f"Tweet posted successfully: {tweet_data['id']}")
            return tweet_data
            
        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}")
            
            # Log error to database
            self.db.log_twitter_action(
                action_type='tweet',
                content=text,
                status='failed',
                error_message=str(e)
            )
            
            return None
    
    def follow_user(self, username: str) -> bool:
        """Follow a user"""
        if not self._check_rate_limit('follows'):
            return False
        
        try:
            username = username.replace('@', '')
            
            if self.client:
                # Get user ID first
                user = self.client.get_user(username=username)
                if user.data:
                    response = self.client.follow_user(user.data.id)
                    success = response.data.get('following', False)
                else:
                    success = False
            
            elif self.api_v1:
                user = self.api_v1.create_friendship(screen_name=username)
                success = user.following
            
            else:
                self.logger.error("No Twitter API client available")
                return False
            
            # Log to database
            self.db.log_twitter_action(
                action_type='follow',
                target_username=username,
                status='success' if success else 'failed',
                response_data={'following': success}
            )
            
            if success:
                self._increment_rate_limit('follows')
                self._add_random_delay(3, 10)
                self.logger.info(f"Successfully followed @{username}")
            else:
                self.logger.warning(f"Failed to follow @{username}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to follow @{username}: {e}")
            
            # Log error to database
            self.db.log_twitter_action(
                action_type='follow',
                target_username=username,
                status='failed',
                error_message=str(e)
            )
            
            return False
    
    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet"""
        if not self._check_rate_limit('likes'):
            return False
        
        try:
            if self.client:
                response = self.client.like(tweet_id)
                success = response.data.get('liked', False)
            
            elif self.api_v1:
                status = self.api_v1.create_favorite(tweet_id)
                success = status.favorited
            
            else:
                self.logger.error("No Twitter API client available")
                return False
            
            # Log to database
            self.db.log_twitter_action(
                action_type='like',
                target_id=tweet_id,
                status='success' if success else 'failed',
                response_data={'liked': success}
            )
            
            if success:
                self._increment_rate_limit('likes')
                self._add_random_delay(1, 4)
                self.logger.info(f"Successfully liked tweet {tweet_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to like tweet {tweet_id}: {e}")
            
            # Log error to database
            self.db.log_twitter_action(
                action_type='like',
                target_id=tweet_id,
                status='failed',
                error_message=str(e)
            )
            
            return False
    
    def retweet(self, tweet_id: str, comment: str = None) -> bool:
        """Retweet a tweet"""
        if not self._check_rate_limit('retweets'):
            return False
        
        try:
            if comment and self.client:
                # Quote tweet
                response = self.client.create_tweet(
                    text=comment,
                    quote_tweet_id=tweet_id
                )
                success = bool(response.data)
            
            elif self.client:
                # Simple retweet
                response = self.client.retweet(tweet_id)
                success = response.data.get('retweeted', False)
            
            elif self.api_v1:
                if comment:
                    # Quote tweet with API v1.1
                    tweet_url = f"https://twitter.com/i/status/{tweet_id}"
                    status = self.api_v1.update_status(f"{comment} {tweet_url}")
                    success = bool(status)
                else:
                    # Simple retweet
                    status = self.api_v1.retweet(tweet_id)
                    success = status.retweeted
            
            else:
                self.logger.error("No Twitter API client available")
                return False
            
            # Log to database
            self.db.log_twitter_action(
                action_type='retweet',
                target_id=tweet_id,
                content=comment,
                status='success' if success else 'failed',
                response_data={'retweeted': success}
            )
            
            if success:
                self._increment_rate_limit('retweets')
                self._add_random_delay(2, 6)
                self.logger.info(f"Successfully retweeted {tweet_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to retweet {tweet_id}: {e}")
            
            # Log error to database
            self.db.log_twitter_action(
                action_type='retweet',
                target_id=tweet_id,
                status='failed',
                error_message=str(e)
            )
            
            return False
    
    def search_tweets(self, query: str, count: int = 10, result_type: str = 'recent') -> List[Dict]:
        """Search for tweets"""
        try:
            tweets = []
            
            if self.client:
                # Use API v2
                response = self.client.search_recent_tweets(
                    query=query,
                    max_results=min(count, 100),
                    tweet_fields=['created_at', 'author_id', 'public_metrics']
                )
                
                if response.data:
                    for tweet in response.data:
                        tweets.append({
                            'id': tweet.id,
                            'text': tweet.text,
                            'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                            'author_id': tweet.author_id,
                            'metrics': tweet.public_metrics
                        })
            
            elif self.api_v1:
                # Use API v1.1
                search_results = self.api_v1.search_tweets(
                    q=query,
                    count=count,
                    result_type=result_type
                )
                
                for tweet in search_results:
                    tweets.append({
                        'id': str(tweet.id),
                        'text': tweet.text,
                        'created_at': tweet.created_at.isoformat(),
                        'author_id': str(tweet.author.id),
                        'author_username': tweet.author.screen_name,
                        'metrics': {
                            'retweet_count': tweet.retweet_count,
                            'favorite_count': tweet.favorite_count
                        }
                    })
            
            self.logger.info(f"Found {len(tweets)} tweets for query: {query}")
            return tweets
            
        except Exception as e:
            self.logger.error(f"Failed to search tweets: {e}")
            return []
    
    def auto_engage_with_keywords(self, keywords: List[str] = None) -> Dict[str, int]:
        """Automatically engage with tweets containing keywords"""
        if not keywords:
            keywords = self.retweet_keywords + self.like_keywords
        
        engagement_stats = {
            'tweets_found': 0,
            'likes': 0,
            'retweets': 0,
            'follows': 0,
            'errors': 0
        }
        
        try:
            for keyword in keywords:
                # Search for tweets with keyword
                tweets = self.search_tweets(f"{keyword} -is:retweet", count=5)
                engagement_stats['tweets_found'] += len(tweets)
                
                for tweet in tweets:
                    try:
                        # Like tweet if auto-like is enabled
                        if (self.auto_like_enabled and 
                            any(kw in tweet['text'].lower() for kw in self.like_keywords)):
                            
                            if self.like_tweet(tweet['id']):
                                engagement_stats['likes'] += 1
                        
                        # Retweet if auto-retweet is enabled
                        if (self.auto_retweet_enabled and 
                            any(kw in tweet['text'].lower() for kw in self.retweet_keywords)):
                            
                            if self.retweet(tweet['id']):
                                engagement_stats['retweets'] += 1
                        
                        # Follow author if conditions are met
                        if (self.auto_follow_enabled and 
                            tweet.get('author_username') and
                            random.random() < 0.3):  # 30% chance to follow
                            
                            if self.follow_user(tweet['author_username']):
                                engagement_stats['follows'] += 1
                        
                        # Add delay between actions
                        self._add_random_delay(5, 15)
                        
                    except Exception as e:
                        self.logger.error(f"Error engaging with tweet {tweet['id']}: {e}")
                        engagement_stats['errors'] += 1
                
                # Delay between keyword searches
                self._add_random_delay(10, 30)
            
            self.logger.info(f"Auto-engagement completed: {engagement_stats}")
            return engagement_stats
            
        except Exception as e:
            self.logger.error(f"Auto-engagement failed: {e}")
            engagement_stats['errors'] += 1
            return engagement_stats
    
    def follow_target_accounts(self) -> int:
        """Follow predefined target accounts"""
        followed_count = 0
        
        for account in self.follow_accounts:
            try:
                if self.follow_user(account):
                    followed_count += 1
                
                # Add delay between follows
                self._add_random_delay(10, 30)
                
            except Exception as e:
                self.logger.error(f"Failed to follow {account}: {e}")
        
        return followed_count
    
    def post_success_tweet(self, hashtag: str = None, custom_message: str = None) -> Optional[Dict]:
        """Post success tweet after claiming airdrop"""
        if not self.auto_tweet_success:
            return None
        
        try:
            if custom_message:
                tweet_text = custom_message
            else:
                tweet_text = self.success_tweet_template
                
                if hashtag:
                    tweet_text = tweet_text.replace('{hashtag}', hashtag)
                else:
                    tweet_text = tweet_text.replace('#{hashtag}', '')
            
            # Add timestamp to make tweet unique
            timestamp = datetime.now().strftime('%H:%M')
            tweet_text += f" | {timestamp}"
            
            return self.tweet(tweet_text)
            
        except Exception as e:
            self.logger.error(f"Failed to post success tweet: {e}")
            return None
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """Get user information"""
        try:
            username = username.replace('@', '')
            
            if self.client:
                user = self.client.get_user(
                    username=username,
                    user_fields=['created_at', 'description', 'public_metrics', 'verified']
                )
                
                if user.data:
                    return {
                        'id': user.data.id,
                        'username': user.data.username,
                        'name': user.data.name,
                        'description': user.data.description,
                        'created_at': user.data.created_at.isoformat() if user.data.created_at else None,
                        'verified': user.data.verified,
                        'metrics': user.data.public_metrics
                    }
            
            elif self.api_v1:
                user = self.api_v1.get_user(screen_name=username)
                
                return {
                    'id': str(user.id),
                    'username': user.screen_name,
                    'name': user.name,
                    'description': user.description,
                    'created_at': user.created_at.isoformat(),
                    'verified': user.verified,
                    'metrics': {
                        'followers_count': user.followers_count,
                        'following_count': user.friends_count,
                        'tweet_count': user.statuses_count,
                        'listed_count': user.listed_count
                    }
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get user info for @{username}: {e}")
            return None
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        current_time = time.time()
        status = {}
        
        for action_type, limits in self.rate_limits.items():
            remaining = max(0, limits['limit'] - limits['count'])
            reset_in = max(0, limits['reset_time'] - current_time)
            
            status[action_type] = {
                'limit': limits['limit'],
                'used': limits['count'],
                'remaining': remaining,
                'reset_in_seconds': int(reset_in),
                'reset_at': datetime.fromtimestamp(limits['reset_time']).isoformat()
            }
        
        return status
    
    def reset_rate_limits(self) -> None:
        """Reset all rate limit counters"""
        for action_type in self.rate_limits:
            self.rate_limits[action_type]['count'] = 0
            self.rate_limits[action_type]['reset_time'] = time.time() + 3600
        
        self.logger.info("Rate limits reset")
    
    def get_twitter_session_with_cookies(self) -> requests.Session:
        """Get requests session with Twitter cookies for web scraping"""
        return self.cookie_manager.get_session_with_cookies('twitter.com')
    
    def scrape_twitter_data(self, url: str) -> Optional[Dict]:
        """Scrape Twitter data using cookies (for advanced features)"""
        try:
            session = self.get_twitter_session_with_cookies()
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                # Basic scraping - can be extended based on needs
                return {
                    'url': url,
                    'status_code': response.status_code,
                    'content_length': len(response.content),
                    'scraped_at': datetime.now().isoformat()
                }
            else:
                self.logger.warning(f"Failed to scrape {url}: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Twitter scraping failed: {e}")
            return None
    
    def validate_api_connection(self) -> bool:
        """Validate Twitter API connection"""
        try:
            if self.api_v1:
                user = self.api_v1.verify_credentials()
                self.logger.info(f"Twitter API connection valid for @{user.screen_name}")
                return True
            elif self.client:
                user = self.client.get_me()
                if user.data:
                    self.logger.info(f"Twitter API connection valid for @{user.data.username}")
                    return True
            
            self.logger.error("No valid Twitter API connection")
            return False
            
        except Exception as e:
            self.logger.error(f"Twitter API validation failed: {e}")
            return False
    
    def get_analytics_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get Twitter analytics summary"""
        analytics = self.db.get_analytics(days)
        twitter_stats = analytics.get('twitter', {})
        
        summary = {
            'period_days': days,
            'total_actions': sum(stats.get('total', 0) for stats in twitter_stats.values()),
            'successful_actions': sum(stats.get('successful', 0) for stats in twitter_stats.values()),
            'actions_by_type': twitter_stats,
            'rate_limit_status': self.get_rate_limit_status(),
            'generated_at': datetime.now().isoformat()
        }
        
        if summary['total_actions'] > 0:
            summary['overall_success_rate'] = (
                summary['successful_actions'] / summary['total_actions'] * 100
            )
        else:
            summary['overall_success_rate'] = 0
        
        return summary