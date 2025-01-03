from fastapi import Depends, HTTPException, APIRouter, File, UploadFile, Form, Response
from sqlalchemy.orm import Session
from db import schemas, get_db, models
import api.auth as auth
import base64
from sqlalchemy import func, case
from io import BytesIO
from PIL import Image

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

router = APIRouter()

# create a new post
@router.post("/posts", response_model=schemas.PostCreateResponse)
def create_post(
    post_data: schemas.PostCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):

    # create a new post instance
    new_post = models.Posts(
        user_id=current_user,
        caption=post_data.caption
    )

    # add and commit the post to the database
    try:
        db.add(new_post)
        db.commit()
        db.refresh(new_post)

        return {
            "id": new_post.id,
            "user_id": new_post.user_id,
            "caption": new_post.caption,
            "created_at": new_post.created_at,
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create post: {str(e)}")


#upload an image for the post
@router.post("/posts/image/{post_id}", status_code=200)
async def upload_image(
    post_id: int,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    #check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    #check if user is the owner of the post
    if post.user_id != current_user:
        raise HTTPException(status_code=403, detail="Not authorized to modify this post")

    #check for file type
    if image.content_type not in ["image/jpeg", "image/png"]:
        raise HTTPException(status_code=400, detail="Invalid file type")

    contents = await image.read()

    #check for file size
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size too large")
    
    # Try to open the image using Pillow
    try:
        image = Image.open(BytesIO(contents))
        if image.format not in ["JPEG", "PNG"]:
            raise HTTPException(status_code=400, detail="Invalid file format")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Convert RGBA to RGB
    if image.mode == "RGBA":
        image = image.convert("RGB")

    #convert and encode as JPEG for consistency
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)


    #store the binary data in the database
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post.image = buffer.getvalue()

    try:
        db.commit()
        db.refresh(post)
        return {"message": "Image uploaded successfully"}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Failed to upload image: {e}"
        )
    

#get post image
@router.get("/posts/image/{post_id}", status_code=200)
async def get_image(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)):
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not post.image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        image = Image.open(BytesIO(post.image))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image: {e}")
    

    #encode the image as JPEG
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    return Response(content=buffer.getvalue(), media_type="image/jpeg")

#read all posts information
@router.get("/posts", response_model=list[schemas.PostResponse])
def read_posts(db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)):
    posts = (
        db.query(
            models.Posts.id,
            models.Posts.user_id,
            models.Posts.caption,
            models.Posts.created_at,
            func.count(
                case((models.PostReactions.reaction_type == "LIKE", 1))
            ).label("likes_count"),
            func.count(
                case((models.PostReactions.reaction_type == "DISLIKE", 1))
            ).label("dislikes_count"),
        )
        .outerjoin(models.PostReactions, models.PostReactions.post_id == models.Posts.id)
        .group_by(models.Posts.id)
        .all()
    )

    # Map query results to response model
    return [
        {
            "id": post.id,
            "user_id": post.user_id,
            "caption": post.caption,
            "likes_count": post.likes_count,
            "dislikes_count": post.dislikes_count,
            "created_at": post.created_at,
        }
        for post in posts
    ]


#read post information by post_id
@router.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)):

    # Get the post by ID
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    # Check if post exists
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Count likes and dislikes for the post
    likes_count = db.query(func.count(models.PostReactions.id)).filter(
        models.PostReactions.post_id == post.id,
        models.PostReactions.reaction_type == "LIKE"
    ).scalar()

    dislikes_count = db.query(func.count(models.PostReactions.id)).filter(
        models.PostReactions.post_id == post.id,
        models.PostReactions.reaction_type == "DISLIKE"
    ).scalar()

    # Return the response
    return {
        "id": post.id,
        "user_id": post.user_id,
        "caption": post.caption,
        "likes_count": likes_count,
        "dislikes_count": dislikes_count,
        "created_at": post.created_at,
    }

# read all posts information by a user
@router.get("/users/posts/{user_id}", response_model=list[schemas.PostResponse])
def read_user_posts(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: int = Depends(auth.decode_jwt)
):
    # check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Query posts with aggregated likes and dislikes count
    posts = (
        db.query(
            models.Posts.id,
            models.Posts.user_id,
            models.Posts.caption,
            models.Posts.created_at,
            func.count(
                case((models.PostReactions.reaction_type == "LIKE", 1))
            ).label("likes_count"),
            func.count(
                case((models.PostReactions.reaction_type == "DISLIKE", 1))
            ).label("dislikes_count"),
        )\
        .filter(models.Posts.user_id == user_id)
        .outerjoin(models.PostReactions, models.PostReactions.post_id == models.Posts.id)
        .group_by(models.Posts.id)
        .all()
    )

    return [
        {
            "id": post.id,
            "user_id": post.user_id,
            "caption": post.caption,
            "likes_count": post.likes_count,
            "dislikes_count": post.dislikes_count,
            "created_at": post.created_at,
        }
        for post in posts
    ]


# update a post by id
@router.put("/posts/{post_id}", response_model=schemas.PostUpdate)
def update_post(
    post_id: int,
    post: schemas.PostUpdate,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the post by id
    post_db = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    # check if post exists
    if not post_db:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user is the owner of the post
    if post_db.user_id != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this post"
        )
    

    # update the post
    try:
        post_db.caption = post.caption
        db.commit()
        db.refresh(post_db)

        return {
            "caption": post_db.caption
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update post: {str(e)}")


# delete a post by id
@router.delete("/posts/{post_id}", status_code=200)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the post by id
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user is the owner of the post
    if post.user_id != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this post"
        )

    # delete the post
    try:
        db.delete(post)
        db.commit()
        return {"detail": "Post deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete post: {str(e)}")


# like and unlike a post
@router.post("/posts/like/{post_id}", response_model=schemas.PostReactionResponse)
def toggle_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    

    # check if the user has liked the post
    like = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "LIKE",
        )
        .first()
    )

    # unlike the post if the user has liked it
    if like:
        try:
            response = schemas.PostReactionResponse(
                id=like.id,
                user_id=like.user_id, 
                post_id=like.post_id,
                message="Post unliked successfully"
            )
            db.delete(like)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to unlike post: {str(e)}"
            )
        
    #check if the user disliked the post
    dislike = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "DISLIKE",
        )
        .first()
    )

    # remove dislike if the user has disliked the post
    if dislike:
        try:
            response = schemas.PostReactionResponse(
                id=dislike.id,
                user_id=dislike.user_id, 
                post_id=dislike.post_id,
                message="Dislike removed successfully"
            )
            db.delete(dislike)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to remove dislike: {str(e)}"
            )

    # like the post if the user has not liked it
    new_like = models.PostReactions(user_id=current_user, post_id=post_id, reaction_type="LIKE")

    try:
        db.add(new_like)
        db.commit()
        db.refresh(new_like)

        response = schemas.PostReactionResponse(
            id=new_like.id,
            user_id=new_like.user_id, 
            post_id=new_like.post_id,
            message="Post liked successfully"
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to like post: {str(e)}")

# dislike and remove dislike
@router.post("/posts/dislike/{post_id}", response_model=schemas.PostResponse)
def toggle_dislike(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # check if the user has liked the post


    # check if the user has disliked the post
    dislike = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "DISLIKE",
        )
        .first()
    )

    # undo the dislike if the user has liked it
    if dislike:
        try:
            response = schemas.PostReactionResponse(
                id=dislike.id,
                user_id=dislike.user_id, 
                post_id=dislike.post_id,
                message="Dislike removed successfully"
            )
            db.delete(dislike)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to remove dislike: {str(e)}"
            )
        
    #check if the user liked the post
    like = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "LIKE",
        )
        .first()
    )

    # remove like if the user has liked the post
    if like:
        try:
            response = schemas.PostReactionResponse(
                id=like.id,
                user_id=like.user_id, 
                post_id=like.post_id,
                message="Like removed successfully"
            )
            db.delete(like)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to remove like: {str(e)}")

    # like the post if the user has not liked it
    new_dislike = models.PostReactions(user_id=current_user, post_id=post_id, reaction_type="dislike")

    try:
        db.add(new_dislike)
        db.commit()
        db.refresh(new_dislike)
        response = schemas.PostReactionResponse(
            id=new_dislike.id,
            user_id=new_dislike.user_id, 
            post_id=new_dislike.post_id,
            message="Post disliked successfully"
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to like post: {str(e)}")
    
# display all likes for a post
@router.get("/posts/likes/{post_id}", response_model=list[schemas.PostReactionResponse])
def read_post_likes(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all likes for a post
    likes = db.query(models.PostReactions).filter(
        models.PostReactions.post_id == post_id,
        models.PostReactions.reaction_type == "LIKE"
        ).all()
    return likes

# display all dislikes for a post
@router.get("/posts/dislikes/{post_id}", response_model=list[schemas.PostReactionResponse])
def read_post_dislikes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all likes for a post
    dislikes = db.query(models.PostReactions).filter(
        models.PostReactions.post_id == post_id,
        models.PostReactions.reaction_type == "DISLIKE"
        ).all()
    return dislikes


# count the number of likes for a post
@router.get("/posts/likes/count/{post_id}", response_model=int)
def count_post_likes(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # count the number of likes for a post
    count = (
        db.query(models.PostReactions).filter(
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "LIKE"
            ).count()
    )
    return count

# count the number of dislikes for a post
@router.get("/posts/dislikes/count/{post_id}", response_model=int)
def count_post_dislikes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # count the number of likes for a post
    count = (
        db.query(models.PostReactions).filter(
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "DISLIKE"
            ).count()
    )
    return count



# check if a user has liked a post
@router.get("/posts/like/{post_id}", response_model=bool)
def check_user_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    like = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "LIKE"
        )
        .first()
    )
    if like:
        return True
    return False

# check if a user has disliked a post
@router.get("/posts/dislike/{post_id}", response_model=bool)
def check_user_dislike(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # check if the user has liked the post
    dislike = (
        db.query(models.PostReactions)
        .filter(
            models.PostReactions.user_id == current_user,
            models.PostReactions.post_id == post_id,
            models.PostReactions.reaction_type == "DISLIKE"
        )
        .first()
    )
    if dislike:
        return True
    return False


# read all users who liked a post
@router.get("/posts/likedby/{post_id}", response_model=list[schemas.UserResponse])
def read_post_likedby(post_id: int, db: Session = Depends(get_db), current_user: int = Depends(auth.decode_jwt)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who liked a post
    users = (
        db.query(models.User)
        .join(models.PostReactions)
        .filter(models.PostReactions.post_id == post_id,
                models.PostReactions.reaction_type == "LIKE"
                )
        .all()
    )
    return users
   

# read all users who disliked a post
@router.get("/posts/dislikedby/{post_id}", response_model=list[schemas.UserResponse])
def read_post_dislikedby(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who liked a post
    users = (
        db.query(models.User)
        .join(models.PostReactions)
        .filter(models.PostReactions.post_id == post_id,
                models.PostReactions.reaction_type == "DISLIKE"
                )
        .all()
    )
    return users
   

