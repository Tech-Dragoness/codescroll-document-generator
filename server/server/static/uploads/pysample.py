def handle_creature(creature):
    match creature:
        case "dragon":
            print("🔥 Beware the dragon's breath!")
        case "unicorn":
            print("🦄 A symbol of purity and grace.")
        case "goblin":
            print("👺 Mischievous and greedy.")
        case _:
            print("✨ Unknown magical creature.")

handle_creature("dragon")
