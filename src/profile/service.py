from sqlalchemy.orm import Session
from auth.models import User,Follow
from activity.models import Activity
from .schemas import FollowersList,FollowingList,Profile
from auth.service import get_current_user,existing_user,get_user_from_id

# follow
async def follow_svc(db:Session,follower:str,following:str):
    db_follower=await existing_user(db,follower,"")
    db_following=await existing_user(db,following,"")
    if not db_follower or not db_following:
       return False
    if db_follower.id == db_following.id:
       return False
     
    db_follow=db.query(Follow).filter(
        Follow.follower_id == db_follower.id,
        Follow.following_id == db_following.id
    ).first()
    
    if db_follow:
      return False
    db_follow=Follow(follower_id=db_follower.id,following_id=db_following.id)
    db.add(db_follow)
    db_follower.following_count += 1
    db_following.followers_count += 1
    follow_activity=Activity(username=follower,followed_username=following,followed_user_pic=db_following.profile_pic)
    db.add(follow_activity)
    db.commit()
    return {"message": "Successfully followed user"}
    

# unfollow
async def unfollow_svc(db:Session,follower:str,following:str):
    db_follower=await existing_user(db,follower,"")
    db_following=await existing_user(db,following,"")
    if not db_follower or not db_following:
       return False
    if db_follower.id == db_following.id:
       return False
     
    db_follow=db.query(Follow).filter(
        Follow.follower_id == db_follower.id,
        Follow.following_id == db_following.id
    ).first()
    
    if not db_follow:
       return False
    db.delete(db_follow)
    db_follower.following_count -= 1
    db_following.followers_count -= 1
    db.commit()
    return {"message": "Successfully unfollowed user"}

# get followers
async def get_followers_svc(db:Session,user_id:int,skip:int=0,limit:int=10)->FollowersList:
    db_user= await get_user_from_id(db,user_id)
    if not db_user:
       return []
    db_followers=db.query(Follow).filter_by(following_id=db_user.id).join(User,User.id==Follow.follower_id).offset(skip).limit(limit).all()    
    followers=[]
    for user in db_followers:
        followers.append(
          {
            "username":user.follower.username,
            "name":user.follower.name,
            "profile_pic":user.follower.profile_pic,
          }
        )
    return FollowersList(followers=followers)
        

# get following
async def get_following_svc(db:Session,user_id:int) ->FollowingList:
    db_user= await get_user_from_id(db,user_id)
    if not db_user:
       return []
    db_following=db.query(Follow).filter_by(follower_id=db_user.id).join(User,User.id==Follow.following_id).all()
    following=[]
    for user in db_following:
        following.append(
          {           
            "username":user.following.username,
            "name":user.following.name,
            "profile_pic":user.following.profile_pic,
          }
        )
    return FollowingList(following=following)
    
# check follow activity
async def check_follow_svc(db:Session,current_user:str,user:str):
    db_follower=await existing_user(db,current_user,"")
    db_following=await existing_user(db,user,"")
    
    if not db_follower or not db_following:
       return False
    db_following=db.query(Follow).filter(Follow.follower_id==db_follower.id,Follow.following_id==db_following.id).first()
    if db_following:
        return True
    return False