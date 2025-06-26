extends Button

enum ButtonType {CLEAR, COPY, PASTE}

@export var ctx_menu_packed: PackedScene
@export var ctx_button_packed: PackedScene
@export var ctx_button_types: Array[ButtonType]

var ctx_menu: ContextMenu

func _ready() -> void:
    pressed.connect(_on_pressed)

func _on_pressed():
    Globals.main_node.context_exit.show()
    ctx_menu = ctx_menu_packed.instantiate()
    ctx_menu.global_position = global_position - Vector2(200, -20)
    var ctx_button: Button
    for button_type in ctx_button_types:
        ctx_button = ctx_button_packed.instantiate()
        match button_type:
            ButtonType.CLEAR:
                ctx_button.text = 'clear'
                ctx_button.pressed.connect(_on_clear_pressed)
            ButtonType.COPY:
                ctx_button.text = 'copy'
                ctx_button.pressed.connect(_on_copy_pressed)
            ButtonType.PASTE:
                ctx_button.text = 'paste'
                ctx_button.pressed.connect(_on_paste_pressed)
        ctx_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
        ctx_menu.add_btn(ctx_button)
    Globals.main_node.main_control_node.add_child(ctx_menu)
    Globals.context_menu = ctx_menu

func is_editable(node: Node) -> bool:
    return node is TextEdit or node is LineEdit

func _on_clear_pressed():
    for child in get_parent().get_children():
        if is_editable(child):
            child.call('clear')
            break
    Globals.main_node.context_exit.hide()
    ctx_menu.queue_free()

func _on_copy_pressed():
    for child in get_parent().get_children():
        if is_editable(child):
            DisplayServer.clipboard_set(child.text)
            break
    Globals.main_node.context_exit.hide()
    ctx_menu.queue_free()

func _on_paste_pressed():
    for child in get_parent().get_children():
        if is_editable(child):
            child.text = DisplayServer.clipboard_get()
            break
    Globals.main_node.context_exit.hide()
    ctx_menu.queue_free()
