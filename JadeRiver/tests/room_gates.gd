extends SceneTree
var checks=0
var failures: Array[String]=[]
func _initialize(): call_deferred("run")
func check(ok: bool,label: String):
	checks+=1
	if not ok: failures.append(label)
func run():
	var zone=ZoneGeometry.new()
	zone.configure(ZoneLayout.compile(MapGenerator.generate("village",7)))
	for direction in [-1,1]:
		var x=150.0 if direction<0 else 5250.0
		for rate in [20,30,60,120]:
			for height in [0,100,300]:
				for depth in [790,850,866,880,930]:
					var travel=RoomTravel.new()
					travel.gates=RoomTravel.specs(5400)
					var state=ActorState.new()
					state.surface=zone.index.river_walk if height==0 else null
					state.air_stratum="ground"
					state.altitude=height
					state.plane=Vector2(x-direction*180,depth)
					travel.reset(state.plane,height)
					var exits=0
					for frame in rate*2:
						state.plane.x+=direction*205.0/rate
						var result=travel.advance(state)
						if result!=0:
							exits+=1
							check((state.plane.x-x)*direction>=126,"Whole body must clear gate")
					var expected=1 if depth in [850,866,880] and height<=100 else 0
					check(exits==expected,"Gate direction/rate/height/depth: "+str([direction,rate,height,depth]))
		var travel=RoomTravel.new()
		travel.gates=RoomTravel.specs(5400)
		var state=ActorState.new()
		state.surface=zone.index.river_walk
		state.plane=Vector2(x-direction*180,866)
		travel.reset(state.plane)
		for offset in [-100,0,100,30,-180]:
			state.plane.x=x+direction*offset
			check(travel.advance(state)==0,"Entering and retreating never teleports")
		state.plane=Vector2(x+direction*180,800)
		check(travel.advance(state)==0,"Leaving through side of gate cancels traversal")
		state.plane=Vector2(x+direction*180,866)
		check(travel.advance(state)==0,"Arriving outside gate never triggers it")
	# Gate posts are solid; their open passage remains walkable.
	for x in [150,5250]:
		check(zone.blocks_at(Vector2(x-70,835),0,"ground"),"Rear gate post collision")
		check(zone.blocks_at(Vector2(x+60,908),0,"ground"),"Front gate post collision")
		for y in [850,866,880]:
			for dx in range(-140,141,20): check(not zone.blocks_at(Vector2(x+dx,y),0,"ground"),"Open passage")
	for failure in failures: push_error(failure)
	print("ROOM_GATES: ",checks-failures.size(),"/",checks)
	quit(1 if not failures.is_empty() else 0)
