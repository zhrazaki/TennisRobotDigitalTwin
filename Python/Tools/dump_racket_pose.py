"""Dump world transforms of the player + racket actors.

Workflow:
  1. Arrange the racket by hand in the viewport (move/rotate the
     OpponentPlayer_Racket_* mesh actors until it sits perfectly).
  2. Run: py "<project>/Python/Tools/dump_racket_pose.py"  (Cmd tab, no sys.path needed)
  3. Paste ALL lines starting with POSE back to the assistant.
  4. The assistant bakes them into Court/player_spawner.py so every
     rebuild reproduces your manual pose exactly.
"""

import unreal


def run():
    subsys = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    print("POSE-BEGIN")
    for a in subsys.get_all_level_actors():
        if not a:
            continue
        try:
            label = a.get_actor_label()
        except Exception:
            continue
        if "OpponentPlayer" in label:
            try:
                l = a.get_actor_location()
                r = a.get_actor_rotation()
                s = a.get_actor_scale3d()
                print("POSE %s | loc=(%.2f, %.2f, %.2f) rot=(%.2f, %.2f, %.2f) scale=(%.4f, %.4f, %.4f)" % (
                    label, l.x, l.y, l.z, r.pitch, r.yaw, r.roll, s.x, s.y, s.z))
            except Exception as e:
                print("POSE %s | ERROR %s" % (label, e))
    print("POSE-END")


if __name__ == "__main__":
    run()
