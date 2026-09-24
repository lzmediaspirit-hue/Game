extends SceneTree
var errors: Array[String]=[]
func _initialize(): call_deferred("run")
func check(value: bool,message: String):
	if not value: errors.append(message)
	print("PASS: " if value else "FAIL: ",message)
func touch(id: int,point: Vector2,pressed: bool):
	var e=InputEventScreenTouch.new()
	e.index=id
	e.position=point
	e.pressed=pressed
	root.push_input(e)
func drag(id: int,point: Vector2):
	var e=InputEventScreenDrag.new()
	e.index=id
	e.position=point
	root.push_input(e)
func click(point: Vector2,pressed: bool):
	var e=InputEventMouseButton.new()
	e.position=point
	e.global_position=point
	e.button_index=MOUSE_BUTTON_LEFT
	e.pressed=pressed
	root.push_input(e)
func run():
	if DisplayServer.get_name()=="headless":
		print("Pixel input checks require a window: omit --headless.")
		quit(2)
		return
	var stage=load("res://scenes/pixel_stage.tscn").instantiate()
	root.add_child(stage)
	var main=stage.get_node("GameViewport/JadeRiver")
	main.preview_mode=true
	await process_frame
	main.show_creation(0)
	await process_frame
	click(Vector2(887,557),true)
	click(Vector2(887,557),false)
	await process_frame
	check(main.draft.hair_color==1,"Viewport maps creation clicks to dye swatch")
	main.enter_world(root.get_node("Wardrobe").defaults())
	await process_frame
	touch(1,Vector2(200,530),true)
	drag(1,Vector2(276,530))
	await process_frame
	check(main.world.player.movement.x>0.9,"Viewport maps joystick drag")
	touch(2,Vector2(933,640),true)
	await process_frame
	check(main.world.player.surface==null,"Viewport maps simultaneous jump touch")
	touch(2,Vector2(933,640),false)
	touch(1,Vector2(276,530),false)
	await process_frame
	check(main.world.player.movement==Vector2.ZERO,"Viewport forwards release")
	touch(3,Vector2(1036,634),true)
	drag(3,Vector2(1036,560))
	await process_frame
	check(main.hud.skill_page==1,"Viewport maps skill swipe")
	touch(3,Vector2(1036,560),false)
	check(stage.get_node("GameViewport").size==Vector2i(1280,720),"Native render target preserves artwork and UI detail")
	root.go_back_requested.emit()
	await process_frame
	check(main.screen=="selection","System Back returns through the save-aware handler")
	print("PIXEL_INPUT_TESTS: ",7-errors.size(),"/7 passed")
	quit(0 if errors.is_empty() else 1)



