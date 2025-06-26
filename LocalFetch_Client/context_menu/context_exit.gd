extends Control


func _gui_input(event: InputEvent) -> void:
    if visible and event is InputEventMouseButton and event.is_pressed():
        if Globals.context_menu:
            Globals.context_menu.queue_free()
        hide()
