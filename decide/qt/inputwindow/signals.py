from blinker import Namespace

namespace = Namespace()

actor_created = namespace.signal("actor_created")
actor_changed = namespace.signal("actor_changed")
actor_deleted = namespace.signal("actor_deleted")

issue_created = namespace.signal("issue_created")
issue_changed = namespace.signal("issue_changed")
issue_deleted = namespace.signal("issue_deleted")

actor_issue_created = namespace.signal("actor_issue_created")
actor_issue_changed = namespace.signal("actor_issue_changed")
actor_issue_deleted = namespace.signal("actor_issue_deleted")
