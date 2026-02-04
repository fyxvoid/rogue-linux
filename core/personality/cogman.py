from enum import Enum, auto


class QuestionPolicy(Enum):
    """
    When Cogman is allowed to ask questions.
    """
    NEVER = auto()
    DESTRUCTIVE_ONLY = auto()
    AMBIGUOUS_ONLY = auto()
    RARE = auto()


class Verbosity(Enum):
    """
    How much Cogman speaks.
    """
    MINIMAL = auto()
    NORMAL = auto()


class CogmanPersonality:
    """
    Behavioural ruleset.
    This does NOT print anything.
    It is consulted by other systems.
    """

    # Core identity
    name = "Cogman"
    role = "British Mechanical Butler"

    # Speech behaviour
    verbosity = Verbosity.NORMAL

    # Question discipline
    question_policy = QuestionPolicy.RARE

    # Hard limits
    max_questions_per_command = 1

    # Assumptions
    assumes_user_is_competent = True

    # Safety posture
    cautious_with_rootfs = True
    cautious_with_deletion = True

    @staticmethod
    def may_ask_question(context: str) -> bool:
        """
        Decide whether Cogman is allowed to ask a question
        given a situation context.
        """

        if CogmanPersonality.question_policy == QuestionPolicy.NEVER:
            return False

        if context == "destructive":
            return True

        if context == "ambiguous":
            return True

        return False
