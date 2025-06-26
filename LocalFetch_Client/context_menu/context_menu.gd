class_name ContextMenu
extends Control

@onready var vbox: VBoxContainer = $VBoxContainer

var stored_buttons: Array[Button] = []


func _ready() -> void:
    for button in stored_buttons:
        vbox.add_child(button)

func add_btn(button: Button):
    stored_buttons.append(button)
