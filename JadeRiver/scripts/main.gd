extends Control
const Avatar=preload("res://scripts/avatar.gd")
const World=preload("res://scripts/world.gd")
const Hud=preload("res://scripts/hud.gd")
const Backdrop=preload("res://scripts/backdrop.gd")
const Ornament=preload("res://scripts/ornament.gd")
const GOLD=Color("e2c793")
const PALE=Color("f4ecd5")
var menu: Control
var backdrop: Control
var world: Node2D
var hud: Control
var chosen=0
var draft: Dictionary
var preview: Node2D
var name_field: LineEdit
var row_names: Dictionary={}
var dye_buttons: Array[Button]=[]
var preview_mode=false
var screen="selection"
var ui_font: Font
var launch_override_consumed=false
func _ready():
	get_tree().auto_accept_quit=false
	get_tree().quit_on_go_back=false
	get_tree().root.go_back_requested.connect(return_to_selection)
	get_tree().root.close_requested.connect(save_and_quit)
	var font_variation=FontVariation.new()
	font_variation.base_font=load("res://art/fonts/CormorantGaramond.ttf")
	font_variation.base_font.antialiasing=TextServer.FONT_ANTIALIASING_GRAY
	font_variation.variation_opentype={"wght":500}
	ui_font=font_variation
	var background_layer=CanvasLayer.new()
	background_layer.layer=-10
	add_child(background_layer)
	backdrop=Backdrop.new()
	background_layer.add_child(backdrop)
	show_selection()
	var args=OS.get_cmdline_user_args()
	preview_mode=not args.is_empty()
	if "--preview-selection" in args:
		Wardrobe.slots[0]=Wardrobe.defaults()
		show_selection()
	if "--preview-create" in args: show_creation(0)
	if "--preview-world" in args: enter_world(Wardrobe.defaults())
	if "--preview-roof" in args:
		enter_world(Wardrobe.defaults())
		world.player.plane=Vector2(1240,735)
		world.player.surface=world.by_id("jade_roof")
		world.player.altitude=world.player.surface.height_at(world.player.plane)
	if "--capture" in args:
		await get_tree().create_timer(2.0).timeout
		await RenderingServer.frame_post_draw
		get_tree().root.get_texture().get_image().save_png("res://../"+screen+"-preview.png")
		get_tree().quit()
func style(fill: Color,border=Color("887a5e"),width=1) -> StyleBoxFlat:
	var s=StyleBoxFlat.new()
	s.bg_color=fill
	s.border_color=border
	s.set_border_width_all(width)
	s.set_corner_radius_all(3)
	s.content_margin_left=12
	s.content_margin_right=12
	return s
func label_at(parent: Node,text: String,rect: Rect2,size: int,color=PALE,center=false) -> Label:
	var l=Label.new()
	l.text=text
	l.position=rect.position
	l.size=rect.size
	l.add_theme_font_override("font",ui_font)
	l.add_theme_font_size_override("font_size",size)
	l.add_theme_color_override("font_color",color)
	l.add_theme_color_override("font_shadow_color",Color(0,0,0,0.9))
	l.add_theme_constant_override("shadow_offset_y",2)
	l.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	if center: l.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	l.mouse_filter=Control.MOUSE_FILTER_IGNORE
	parent.add_child(l)
	return l
func button_at(parent: Node,text: String,rect: Rect2,callback: Callable,primary=false) -> Button:
	var b=Button.new()
	b.text=text
	b.position=rect.position
	b.size=rect.size
	b.add_theme_font_override("font",ui_font)
	b.add_theme_font_size_override("font_size",27)
	b.add_theme_color_override("font_color",GOLD)
	b.add_theme_color_override("font_hover_color",PALE)
	b.add_theme_stylebox_override("normal",style(Color(0.045,0.10,0.125,0.94),GOLD if primary else Color("887a5e"),2 if primary else 1))
	b.add_theme_stylebox_override("hover",style(Color("254249"),GOLD,2))
	b.add_theme_stylebox_override("pressed",style(Color("32564e"),GOLD,2))
	b.add_theme_stylebox_override("focus",style(Color(0,0,0,0),GOLD,2))
	b.pressed.connect(callback)
	parent.add_child(b)
	return b
func panel_at(parent: Node,rect: Rect2,selected=false) -> Panel:
	var p=Panel.new()
	p.position=rect.position
	p.size=rect.size
	p.mouse_filter=Control.MOUSE_FILTER_IGNORE
	p.add_theme_stylebox_override("panel",style(Color(0.025,0.065,0.09,0.91),GOLD if selected else Color("80785f"),2))
	parent.add_child(p)
	# Inset border and corner flourishes echo the supplied reference.
	var inset=Panel.new()
	inset.position=Vector2(7,7)
	inset.size=rect.size-Vector2(14,14)
	inset.add_theme_stylebox_override("panel",style(Color(0,0,0,0),Color(0.7,0.6,0.4,0.25),1))
	inset.mouse_filter=Control.MOUSE_FILTER_IGNORE
	p.add_child(inset)
	for corner in [Vector2(12,12),Vector2(rect.size.x-20,12),Vector2(12,rect.size.y-20),rect.size-Vector2(20,20)]:
		var jewel=ColorRect.new()
		jewel.position=corner
		jewel.size=Vector2(8,8)
		jewel.color=GOLD
		jewel.mouse_filter=Control.MOUSE_FILTER_IGNORE
		p.add_child(jewel)
	return p
func clear_menu():
	if is_instance_valid(menu):
		remove_child(menu)
		menu.queue_free()
	menu=Control.new()
	menu.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(menu)
func show_selection():
	screen="selection"
	clear_menu()
	label_at(menu,"JADE RIVER",Rect2(0,35,1280,75),64,GOLD,true)
	label_at(menu,"Choose your disciple",Rect2(0,103,1280,35),29,PALE,true)
	var ornament=Ornament.new()
	menu.add_child(ornament)
	for i in 3:
		var x=121+i*360
		var filled=Wardrobe.slots[i] is Dictionary
		var card=panel_at(menu,Rect2(x,192,318,409),filled and i==chosen)
		var select=button_at(card,"",Rect2(0,0,318,409),func(): select_slot(i))
		select.add_theme_stylebox_override("normal",style(Color(0,0,0,0),Color(0,0,0,0),0))
		select.add_theme_stylebox_override("hover",style(Color(0.2,0.4,0.38,0.09),GOLD,2))
		label_at(card,"◇",Rect2(0,24,318,40),34,GOLD,true)
		if filled:
			var actor=Avatar.new()
			actor.outfit=Wardrobe.slots[i].duplicate()
			actor.position=Vector2(159,275)
			actor.scale=Vector2.ONE*2.0
			card.add_child(actor)
			label_at(card,Wardrobe.slots[i].name,Rect2(15,282,288,40),31,PALE,true)
			label_at(card,Wardrobe.slots[i].sect+" Sect  ·  Mortal",Rect2(15,326,288,30),23,GOLD,true)
			label_at(card,Wardrobe.parts.weapon[Wardrobe.slots[i].weapon].label,Rect2(15,357,288,30),22,Color("aabbb5"),true)
		else:
			label_at(card,"+",Rect2(0,112,318,112),88,GOLD,true)
			label_at(card,"Create Disciple",Rect2(0,241,318,44),32,PALE,true)
	if Wardrobe.slots[chosen] is Dictionary:
		button_at(menu,"ENTER WORLD",Rect2(465,629,350,57),func(): enter_world(Wardrobe.slots[chosen]),true)
func select_slot(index: int):
	chosen=index
	if Wardrobe.slots[index] == null: show_creation(index)
	else: show_selection()
func show_creation(index: int):
	chosen=index
	screen="creation"
	draft=Wardrobe.defaults()
	clear_menu()
	row_names.clear()
	dye_buttons.clear()
	button_at(menu,"‹  Back",Rect2(28,28,135,50),show_selection)
	label_at(menu,"CREATE DISCIPLE",Rect2(230,19,820,68),51,GOLD,true)
	var ornament=Ornament.new()
	ornament.creation=true
	menu.add_child(ornament)
	
	preview=Avatar.new()
	preview.outfit=draft
	preview.position=Vector2(306,532)
	preview.scale=Vector2.ONE*3.0
	menu.add_child(preview)
	label_at(menu,"Idle",Rect2(170,612,275,34),26,GOLD,true)
	var panel=panel_at(menu,Rect2(606,104,628,578),true)
	label_at(panel,"Name",Rect2(29,17,135,42),27,GOLD)
	name_field=LineEdit.new()
	name_field.text=draft.name
	name_field.max_length=24
	name_field.position=Vector2(188,20)
	name_field.size=Vector2(400,40)
	name_field.add_theme_font_override("font",ui_font)
	name_field.add_theme_font_size_override("font_size",25)
	name_field.add_theme_color_override("font_color",PALE)
	name_field.add_theme_stylebox_override("normal",style(Color("0c1b24"),Color("616d67")))
	panel.add_child(name_field)
	var categories=["hair","shirt","pants","shoes","weapon","sect"]
	for i in categories.size():
		var category: String=categories[i]
		var y=70+i*59
		label_at(panel,"Shoe" if category=="shoes" else category.capitalize(),Rect2(28,y,130,61),27,GOLD)
		button_at(panel,"‹",Rect2(190,y+8,43,42),func(): cycle(category,-1))
		row_names[category]=label_at(panel,"",Rect2(242,y,279,58),25,PALE,true)
		button_at(panel,"›",Rect2(537,y+8,43,42),func(): cycle(category,1))
		update_row(category)
	label_at(panel,"Hair dye",Rect2(28,430,145,44),25,GOLD)
	for i in 6:
		var color=Color(Wardrobe.parts._colors.hair[i].hex)
		var swatch=button_at(panel,"",Rect2(191+i*64,434,48,38),func(): set_hair_dye(i))
		swatch.tooltip_text=Wardrobe.parts._colors.hair[i].name
		swatch.add_theme_stylebox_override("normal",style(color,GOLD if i==draft.hair_color else Color("536460"),3 if i==draft.hair_color else 1))
		swatch.add_theme_stylebox_override("hover",style(color,GOLD,3))
		swatch.add_theme_stylebox_override("pressed",style(color,PALE,3))
		dye_buttons.append(swatch)
	button_at(panel,"CREATE DISCIPLE",Rect2(210,510,376,48),create_disciple,true)
	button_at(panel,"Cancel",Rect2(28,510,155,48),show_selection)
func set_hair_dye(index: int):
	draft.hair_color=index
	for i in dye_buttons.size():
		var color=Color(Wardrobe.parts._colors.hair[i].hex)
		dye_buttons[i].add_theme_stylebox_override("normal",style(color,GOLD if i==index else Color("536460"),3 if i==index else 1))
func cycle(category: String,direction: int):
	var options: Array=["Jade","Cloud"] if category=="sect" else Wardrobe.parts[category].keys()
	var index=options.find(draft[category])
	draft[category]=options[posmod(index+direction,options.size())]
	update_row(category)
func update_row(category: String):
	row_names[category].text=draft.sect+" Sect" if category=="sect" else Wardrobe.parts[category][draft[category]].label
func create_disciple():
	draft.name=name_field.text
	var result=Wardrobe.save_slot(chosen,draft)
	if result!=OK:
		name_field.text="Could not save. Please retry."
		return
	show_selection()
func enter_world(outfit: Dictionary):
	screen="world"
	if is_instance_valid(menu):
		remove_child(menu)
		menu.queue_free()
		menu=null
	world=World.new()
	world.outfit=outfit.duplicate(true)
	var progress=outfit.get("progress",{})
	world.map_theme=str(progress.get("map_theme","village"))
	world.map_seed=int(progress.get("map_seed",1))
	if world.map_theme=="":
		# Authored-map saves keep the disciple and resources, entering the new village safely.
		world.map_theme="village"
		var migrated=progress.duplicate(true)
		migrated.merge({"map_revision":World.MAP_REVISION,"map_theme":"village","map_seed":world.map_seed,
			"generator_version":MapGenerator.VERSION,"surface":"river_walk","x":300,"y":850},true)
		world.outfit.progress=migrated
	if not launch_override_consumed:
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--map-theme="): world.map_theme=arg.trim_prefix("--map-theme=")
			if arg.begins_with("--map-seed="): world.map_seed=int(arg.trim_prefix("--map-seed="))
		launch_override_consumed=true
	mount_world()
	var layer=CanvasLayer.new()
	layer.name="MobileHUD"
	add_child(layer)
	hud=Hud.new()
	hud.player=world.player
	hud.skill_page=world.skill_page
	hud.page_changed.connect(func(page): world.skill_page=page)
	layer.add_child(hud)
func change_region(theme: String,seed_value: int,direction: int):
	if screen!="world" or not is_instance_valid(world): return
	var appearance=world.player.avatar.outfit.duplicate(true)
	var entry=RoomTravel.arrival(MapGenerator.WIDTH,direction)
	appearance.progress={"map_revision":World.MAP_REVISION,"map_theme":theme,"map_seed":seed_value,
		"generator_version":MapGenerator.VERSION,"surface":"river_walk","x":entry.x,
		"y":entry.y,"hp":world.player.hp,"qi":world.player.qi,"facing":direction,"skill_page":world.skill_page}
	world.save_game()
	var movement=world.player.movement
	var joystick_engaged=world.player.joystick_engaged
	var sprint_time=world.player.drag_seconds
	var sprint_direction=world.player.sprint_direction
	var was_sprinting=world.player.sprinting
	remove_child(world)
	world.queue_free()
	world=World.new()
	world.outfit=appearance
	world.map_theme=theme
	world.map_seed=seed_value
	mount_world()
	hud.player=world.player
	world.player.movement=movement
	world.player.joystick_engaged=joystick_engaged
	world.player.drag_seconds=sprint_time
	world.player.sprint_direction=sprint_direction
	world.player.sprinting=was_sprinting
	world.save_game()
func mount_world():
	# Initial entry and region travel share lifecycle bindings.
	world.transitions_enabled=world.map_theme!=""
	world.region_exit.connect(change_region,CONNECT_DEFERRED)
	world.save_slot_index=-1 if preview_mode else chosen
	add_child(world)
	backdrop.world=world
func _notification(what):
	if what in [NOTIFICATION_APPLICATION_PAUSED,NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_WM_CLOSE_REQUEST]:
		if is_instance_valid(world) and screen=="world": world.save_game()
func _unhandled_key_input(event):
	if event.pressed and event.keycode==KEY_ESCAPE: return_to_selection()
func return_to_selection():
	if screen=="world":
		world.save_game()
		backdrop.world=null
		remove_child(world)
		world.queue_free()
		var layer=get_node("MobileHUD")
		remove_child(layer)
		layer.queue_free()
	show_selection()



func save_and_quit():
	if screen=="world" and is_instance_valid(world): world.save_game()
	get_tree().quit()
