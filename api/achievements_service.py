from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from db import models
from api import milestones


class AchievementService:
    @staticmethod
    def check_achievements(user_id: int, db: Session) -> List[dict]:
        """
        Checks all possible achievements for a user and awards any new ones.
        Returns a list of newly awarded achievements.
        """
        new_achievements = []

        # Get user's current achievements to avoid rewarding duplicates
        existing_achievements = (
            db.query(models.UserAchievements)
            .filter(models.UserAchievements.user_id == user_id)
            .all()
        )
        existing_achievement_ids = {ua.achievement_id for ua in existing_achievements}

        # Check each achievement type
        quest_achievements = AchievementService._check_quest_achievements(
            user_id, existing_achievement_ids, db
        )
        friend_achievements = AchievementService._check_friend_achievements(
            user_id, existing_achievement_ids, db
        )
        like_achievements = AchievementService._check_like_achievements(
            user_id, existing_achievement_ids, db
        )
        verification_achievements = AchievementService._check_verification_achievements(
            user_id, existing_achievement_ids, db
        )

        new_achievements.extend(quest_achievements)
        new_achievements.extend(friend_achievements)
        new_achievements.extend(like_achievements)
        new_achievements.extend(verification_achievements)

        # Award tokens for new achievements
        if new_achievements:
            AchievementService._award_achievement_tokens(user_id, new_achievements, db)

        return new_achievements

    @staticmethod
    def _check_quest_achievements(
        user_id: int, existing_achievement_ids: set, db: Session
    ) -> List[dict]:
        """Check achievements related to completing quests."""
        new_achievements = []
        completed_quests = (
            db.query(models.UserQuests)
            .filter(
                models.UserQuests.user_id == user_id, models.UserQuests.is_done == True
            )
            .count()
        )

        for milestone, achievement in milestones.QUEST_MILESTONES.items():
            if (
                completed_quests >= milestone
                and achievement["id"] not in existing_achievement_ids
            ):
                new_achievements.append(achievement)

        return new_achievements

    @staticmethod
    def _check_friend_achievements(
        user_id: int, existing_achievement_ids: set, db: Session
    ) -> List[dict]:
        """Check achievements related to making friends."""
        new_achievements = []
        friend_count = len(models.Friends.get_friends(user_id, db))

        for milestone, achievement in milestones.FRIEND_MILESTONES.items():
            if (
                friend_count >= milestone
                and achievement["id"] not in existing_achievement_ids
            ):
                new_achievements.append(achievement)

        return new_achievements

    @staticmethod
    def _check_like_achievements(
        user_id: int, existing_achievement_ids: set, db: Session
    ) -> List[dict]:
        """Check achievements related to receiving likes on posts."""
        new_achievements = []

        # Count total likes received on all user's posts
        total_likes = (
            db.query(func.count(models.PostReactions.id))
            .join(
                models.Posts,
                models.Posts.id == models.PostReactions.post_id,
            )
            .filter(
                models.Posts.user_id == user_id,
                models.PostReactions.reaction_type == "LIKE",
            )
            .scalar()
        )

        for milestone, achievement in milestones.LIKE_MILESTONES.items():
            if (
                total_likes >= milestone
                and achievement["id"] not in existing_achievement_ids
            ):
                new_achievements.append(achievement)

        return new_achievements

    @staticmethod
    def _check_verification_achievements(
        user_id: int, existing_achievement_ids: set, db: Session
    ) -> List[dict]:
        """Check achievements related to verifying other users' quests."""
        new_achievements = []

        verifications_count = (
            db.query(models.QuestVerification)
            .filter(models.QuestVerification.verifier_id == user_id)
            .count()
        )

        for milestone, achievement in milestones.VERIFICATION_MILESTONES.items():
            if (
                verifications_count >= milestone
                and achievement["id"] not in existing_achievement_ids
            ):
                new_achievements.append(achievement)

        return new_achievements

    @staticmethod
    def _award_achievement_tokens(
        user_id: int, achievements: List[dict], db: Session
    ) -> None:
        """Award tokens for newly earned achievements."""
        total_tokens = sum(achievement["award_tokens"] for achievement in achievements)

        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user:
            user.tokens += total_tokens

            # Record each new achievement
            for achievement in achievements:
                new_user_achievement = models.UserAchievements(
                    user_id=user_id, achievement_id=achievement["id"]
                )
                db.add(new_user_achievement)

            db.commit()
