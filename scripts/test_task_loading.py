from harness.task import load_task_spec


def main():
    task = load_task_spec("tasks/fix_bug_no_peeking")

    print("=" * 80)
    print(f"TASK NAME: {task.name}")

    print("=" * 80)
    print("DESCRIPTION:")
    print(task.description)

    print("=" * 80)
    print("BRIEFING:")
    print(task.briefing)

    print("=" * 80)
    print("RULES:")
    for rule in task.rules:
        print(f"- {rule}")

    print("=" * 80)
    print("SCORING-RELEVANT FILES:")
    print(f"Allowed to modify: {task.allowed_to_modify}")
    print(f"Protected files: {task.protected_files}")
    print(f"Forbidden to read: {task.forbidden_to_read}")

    print("=" * 80)
    print("SUCCESS CRITERIA:")
    for criterion in task.success_criteria:
        print(f"- {criterion}")


if __name__ == "__main__":
    main()