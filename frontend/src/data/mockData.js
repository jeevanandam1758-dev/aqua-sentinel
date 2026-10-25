export const detections=[
 {id:1,class_name:'ghost_net',confidence:.96,bbox:{x:120,y:80,width:180,height:120},risk:'HIGH',location:'Port 34.2m'},
 {id:2,class_name:'shipwreck',confidence:.88,bbox:{x:365,y:245,width:155,height:110},risk:'MEDIUM',location:'Starboard 41.7m'},
 {id:3,class_name:'submarine_pipeline',confidence:.94,bbox:{x:220,y:405,width:280,height:54},risk:'LOW',location:'Track 12.3m'},
 {id:4,class_name:'mine_cylinder',confidence:.82,bbox:{x:60,y:315,width:90,height:90},risk:'HIGH',location:'Port 18.6m'}]
export const scans=[
 {id:'SCAN-0248',filename:'coastal_survey_118.jpg',date:'10 Sep 2026',objects:4,risk:'HIGH',confidence:92,status:'COMPLETE'},
 {id:'SCAN-0247',filename:'harbor_sector_c.png',date:'09 Sep 2026',objects:2,risk:'MEDIUM',confidence:89,status:'COMPLETE'},
 {id:'SCAN-0246',filename:'reef_corridor_04.tif',date:'09 Sep 2026',objects:1,risk:'LOW',confidence:94,status:'COMPLETE'},
 {id:'SCAN-0245',filename:'bay_patrol_220.jpg',date:'08 Sep 2026',objects:3,risk:'HIGH',confidence:88,status:'COMPLETE'},
 {id:'SCAN-0244',filename:'channel_grid_07.png',date:'07 Sep 2026',objects:0,risk:'LOW',confidence:91,status:'COMPLETE'}]
export const trend=[{name:'Apr',scans:74},{name:'May',scans:96},{name:'Jun',scans:82},{name:'Jul',scans:126},{name:'Aug',scans:114},{name:'Sep',scans:151}]
export const classes=[{name:'Ghost net',value:96},{name:'Pipeline',value:84},{name:'Shipwreck',value:62},{name:'Mine cyl.',value:41}]
