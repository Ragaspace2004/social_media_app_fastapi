from sqlalchemy.orm import Session
from sqlalchemy import desc
import re
from .schemas import PostCreate,Post as PostSchema, Hashtag
from auth.schemas import User as UserSchema
from .models import Post,post_hashtags,Hashtag
from auth.models import User
from activity.models import Activity
from security_utils import sanitizer

#create hashtag
async def create_hashtag_svc(db:Session,post:Post):
    regex=r"#\w+"
    matches=re.findall(regex,post.content)
    for match in matches:
        name=match[1:]
        hashtag=db.query(Hashtag).filter(Hashtag.name==name).first()
        if not hashtag:
           hashtag=Hashtag(name=name)
           db.add(hashtag)
           db.commit()
        post.hashtags.append(hashtag)
                

#create a post
async def create_post_svc(db:Session,post:PostCreate,user_id:int):
    # Additional sanitization at service layer (defense in depth)
    sanitized_content = sanitizer.sanitize_html(post.content) if post.content else ""
    sanitized_image = sanitizer.sanitize_html(post.image) if post.image else None
    sanitized_location = sanitizer.sanitize_html(post.location) if post.location else None
    
    db_post=Post(
      content=sanitized_content,
      image=sanitized_image,
      location=sanitized_location,
      author_id=user_id
      )
    await create_hashtag_svc(db,db_post)
    db.add(db_post)
    db.commit()
    return db_post

#get user's post
async def get_user_posts_svc(db:Session,user_id:int)->list[PostSchema]:
    posts=db.query(Post).filter(Post.author_id==user_id).order_by(desc(Post.created_at)).all()
    return posts
  
# get posts from a hashtag
async def get_posts_from_hashtag_svc(db:Session,hashtag_name:str):
    hashtag=db.query(Hashtag).filter(Hashtag.name==hashtag_name).first()
    if not hashtag:
      return None
    return hashtag.posts

#get user from username
async def get_user_from_username(db:Session,username:str):
    return db.query(User).filter(User.username==username).first()
  
#get random posts for feeds
async def get_random_posts_svc(db:Session,page:int=1,limit:int=10,hashtag:str=None):
    total_posts=db.query(Post).count()
    offset=(page-1)*limit
    if offset >=total_posts:
        return []
    posts=db.query(Post,User.username).join(User).order_by(desc(Post.created_at))
    
    if hashtag:
      posts=posts.join(post_hashtags).join(Hashtag).filter(Hashtag.name==hashtag)
    posts=posts.offset(offset).limit(limit).all()
    result=[]
    for post,username in posts:
        post_dict=post.__dict__
        post_dict["username"]=username
        result.append(post_dict)
    return result
  
# get post by post_id
async def get_post_from_post_id_svc(db:Session,post_id:int)->PostSchema:
    return db.query(Post).filter(Post.id==post_id).first()
  
# delete post 
async def delete_post_svc(db:Session,post_id:int):
   post=await get_post_from_post_id_svc(db, post_id)
   db.delete(post)
   db.commit()
    
# like a post
async def like_post_svc(db:Session,post_id:int,username:str):
    post = await get_post_from_post_id_svc(db, post_id)
    if not post:
        return False,"invalid post"
    user = db.query(User).filter(User.username==username).first()  # Remove await here
    if not user:
        return False,"invalid user"
    if user in post.liked_by_users:
        return False,"already liked"
    post.liked_by_users.append(user)
    post.likes_count = len(post.liked_by_users)
    
    # activity 
    like_activity = Activity(
        username=post.author.username,
        liked_post_id=post_id,
        username_liked=username,  # Fix: was username_like
        liked_post_image=post.image
    )
    db.add(like_activity)
    db.commit()
    return True,"Post liked successfully"
  
# unlike a post
async def unlike_post_svc(db:Session,post_id:int,username:str):
    post = await get_post_from_post_id_svc(db, post_id)
    if not post:
       return False,"invalid post"
    user = db.query(User).filter(User.username==username).first()  # Remove await here
    if not user:
       return False,"invalid user"
    if user not in post.liked_by_users:  # Fix: use 'not in'
       return False,"already not liked"
    post.liked_by_users.remove(user)
    post.likes_count = len(post.liked_by_users)  # Use likes_count to match your model
    db.commit()
    return True,"Post unliked successfully"  # Add return statement

#users who liked a post
async def liked_users_post_svc(db:Session,post_id:int)->list[UserSchema]:
    post = await get_post_from_post_id_svc(db,post_id)
    if not post:
       return []
    liked_users=post.liked_by_users
    return liked_users



