from blinker import Namespace

namespace = Namespace()

settings_changed = namespace.signal("settings_changed")

actor_selection_changed = namespace.signal("actor_selection_changed")

issue_selection_changed = namespace.signal("issue_selection_changed")
