from fastapi import Depends, HTTPException, APIRouter, File, UploadFile, Form
from sqlalchemy.orm import Session
from db import schemas, get_db, models
import api.auth as auth
import base64
from io import BytesIO
from PIL import Image
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response

router = APIRouter()  # create an instance of the APIRouter class

# Example max file size: 5 MB (Adjust as needed)
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png"]


def get_quest_id_from_user_quest_id(user_quest_id: int, db: Session):
    # get user quest object
    user_quest = (
        db.query(models.UserQuests)
        .filter(models.UserQuests.id == user_quest_id)
        .first()
    )
    return user_quest.quest_id


@router.post("/posts", response_model=schemas.PostResponse)
def create_post(
    caption: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    quest_id: int = Form(...),
    current_user: int = Depends(auth.decode_jwt),
):
    try:
        # 0 Check if the user has a post for this quest+id already
        user_quest = (
            db.query(models.UserQuests)
            .filter(
                models.UserQuests.user_id == current_user,
                models.UserQuests.quest_id == quest_id,
            )
            .first()
        )
        if user_quest is not None:
            raise HTTPException(status_code=400, detail="User has already submitted.")

        # 1) Validate file type
        if image.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400, detail="Invalid file type. Only JPEG or PNG allowed."
            )

        # 2) Read the raw file contents
        contents = image.file.read()

        # 3) Check file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="File size too large.")

        # 4) Convert the uploaded file to a JPEG in memory
        try:
            input_image = Image.open(BytesIO(contents))
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to process image.")

        # Convert to JPEG for consistency
        buffer = BytesIO()
        # You can adjust quality as needed
        input_image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        image_data = buffer.getvalue()

        # 5) Create a new UserQuests entry for this user + quest (mark it done)

        new_user_quest = models.UserQuests(
            user_id=current_user, quest_id=quest_id, is_done=True
        )
        db.add(new_user_quest)
        # Flush so we get new_user_quest.id without committing
        db.flush()

        # 6) Create the Post referencing the user_quest_id
        new_post = models.Posts(
            user_id=current_user,
            caption=caption,
            image=image_data,  # Storing the binary data in DB
            user_quest_id=new_user_quest.id,
        )

        db.add(new_post)
        # (Optional) flush again here, or just do a single flush at the end
        db.flush()
        # update new_user_quest with post_id
        new_user_quest.post_id = new_post.id

        # 7) Commit the transaction
        db.commit()

        # 8) Refresh to get the final state (including generated IDs)
        db.refresh(new_post)
        return schemas.PostResponse(
            id=new_post.id,
            user_id=new_post.user_id,
            caption=new_post.caption,
            created_at=new_post.created_at,
            image_url=f"/posts/image/{new_post.id}",
            quest_id=quest_id,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to create post: {str(e)}")


# read all posts
@router.get("/posts", response_model=list[schemas.PostResponse])
def read_posts(db: Session = Depends(get_db)):
    # get all posts from the database
    posts = db.query(models.Posts).all()

    # decode the image as base64
    for post in posts:
        if post.image:
            post.image = base64.b64encode(post.image).decode("utf-8")

    return posts


# read a post by id
@router.get("/posts/{post_id}", response_model=schemas.PostResponse)
def read_post(post_id: int, db: Session = Depends(get_db)):
    # get the post by id
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()

    # check if post exists
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # decode the image as base64
    if post.image:
        post.image = base64.b64encode(post.image).decode("utf-8")

    return post


# read all posts by a user
@router.get("/users/{user_id}/posts", response_model=list[schemas.PostResponse])
def read_user_posts(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # get all posts by a user
    posts = db.query(models.Posts).filter(models.Posts.user_id == user_id).all()

    return [
        schemas.PostResponse(
            id=post.id,
            user_id=post.user_id,
            caption=post.caption,
            created_at=post.created_at,
            image_url=f"/posts/image/{post.id}",
            quest_id=get_quest_id_from_user_quest_id(post.user_quest_id, db),
        )
        for post in posts
    ]


# update a post by id
@router.put("/posts/{post_id}", response_model=schemas.PostResponse)
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

    # decode the image as base64
    if post_db.image:
        image_base64 = base64.b64encode(post_db.image).decode("utf-8")

    # update the post
    try:
        post_db.caption = post.caption
        db.commit()
        db.refresh(post_db)

        return {
            "id": post_db.id,
            "user_id": post_db.user_id,
            "caption": post_db.caption,
            "created_at": post_db.created_at,
            "image": image_base64,
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
@router.post("/posts/{post_id}/like", response_model=schemas.PostLikeResponse)
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
        db.query(models.PostLikes)
        .filter(
            models.PostLikes.user_id == current_user,
            models.PostLikes.post_id == post_id,
        )
        .first()
    )

    # unlike the post if the user has liked it
    if like:
        try:
            response = schemas.PostLikeResponse(
                id=like.id,
                user_id=like.user_id,
                post_id=like.post_id,
                message="Post unliked successfully",
            )
            db.delete(like)
            db.commit()
            return response
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to unlike post: {str(e)}"
            )

    # like the post if the user has not liked it
    new_like = models.PostLikes(user_id=current_user, post_id=post_id)

    try:
        db.add(new_like)
        db.commit()
        db.refresh(new_like)
        return new_like

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to like post: {str(e)}")


# display all likes for a post
@router.get("/posts/{post_id}/likes", response_model=list[schemas.PostLikeResponse])
def read_post_likes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all likes for a post
    likes = db.query(models.PostLikes).filter(models.PostLikes.post_id == post_id).all()
    return likes


# count the number of likes for a post
@router.get("/posts/{post_id}/likes/count", response_model=int)
def count_post_likes(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # count the number of likes for a post
    count = (
        db.query(models.PostLikes).filter(models.PostLikes.post_id == post_id).count()
    )
    return count


# check if a user has liked a post
@router.get("/posts/{post_id}/like", response_model=bool)
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
        db.query(models.PostLikes)
        .filter(
            models.PostLikes.user_id == current_user,
            models.PostLikes.post_id == post_id,
        )
        .first()
    )
    if like:
        return True
    return False


# read all users who liked a post
@router.get("/posts/{post_id}/likedby", response_model=list[schemas.UserResponse])
def read_post_likedby(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all users who liked a post
    users = (
        db.query(models.User)
        .join(models.PostLikes)
        .filter(models.PostLikes.post_id == post_id)
        .all()
    )
    return users


# comment on a post
@router.post("/posts/{post_id}/comment", response_model=schemas.PostCommentResponse)
def create_comment(
    post_id: int,
    comment: schemas.PostCommentCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # create a new comment instance
    new_comment = models.PostComments(
        user_id=current_user, post_id=post_id, content=comment.content
    )

    # add and commit the comment to the database
    try:
        db.add(new_comment)
        db.commit()
        db.refresh(new_comment)
        return new_comment
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to create comment: {str(e)}"
        )


# read all comments for a post
@router.get(
    "/posts/{post_id}/comments", response_model=list[schemas.PostCommentResponse]
)
def read_post_comments(post_id: int, db: Session = Depends(get_db)):
    # check if post exists
    post = db.query(models.Posts).filter(models.Posts.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # get all comments for a post
    comments = (
        db.query(models.PostComments)
        .filter(models.PostComments.post_id == post_id)
        .all()
    )
    return comments


# read comment by id
@router.get("/comments/{comment_id}", response_model=schemas.PostCommentResponse)
def read_comment(comment_id: int, db: Session = Depends(get_db)):
    # get the comment by id
    comment = (
        db.query(models.PostComments)
        .filter(models.PostComments.id == comment_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


# update a comment by id
@router.put("/comments/{comment_id}", response_model=schemas.PostCommentResponse)
def update_comment(
    comment_id: int,
    comment: schemas.PostCommentCreate,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the comment by id
    comment_db = (
        db.query(models.PostComments)
        .filter(models.PostComments.id == comment_id)
        .first()
    )
    if not comment_db:
        raise HTTPException(status_code=404, detail="Comment not found")

    # check if the user is the owner of the comment
    if comment_db.user_id != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this comment"
        )

    # update the comment
    try:
        comment_db.content = comment.content
        db.commit()
        db.refresh(comment_db)

        return comment_db

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to update comment: {str(e)}"
        )


# delete a comment by id
@router.delete("/comments/{comment_id}", status_code=200)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: int = Depends(auth.decode_jwt),
):
    # get the comment by id
    comment = (
        db.query(models.PostComments)
        .filter(models.PostComments.id == comment_id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # check if the user is the owner of the comment
    if comment.user_id != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of this comment"
        )

    # delete the comment
    try:
        db.delete(comment)
        db.commit()
        return {"detail": "Comment deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to delete comment: {str(e)}"
        )


@router.get("/posts/image/{post_id}", status_code=200)
async def get_post_image(post_id: int, db: Session = Depends(get_db)):
    post: models.Posts = (
        db.query(models.Posts).filter(models.Posts.id == post_id).first()
    )
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.image is None:
        raise HTTPException(status_code=404, detail="Picture not found")

    # Decode the binary data to an image
    try:
        image = Image.open(BytesIO(post.image))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to process image")

    # Encode the image as JPEG
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)

    # Return the JPEG image
    return Response(content=buffer.getvalue(), media_type="image/jpeg")
