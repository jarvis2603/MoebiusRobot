import { useEffect, useRef, useState } from 'react';
import { Badge, Button, Card } from 'react-bootstrap';
import ROSLIB from 'roslib';

const MAP_TOPIC = import.meta.env.VITE_MAP_TOPIC || '/map';
const SCAN_TOPIC = import.meta.env.VITE_SCAN_TOPIC || '/scan';
const PLAN_TOPIC = import.meta.env.VITE_PLAN_TOPIC || '/plan';
const LOCAL_PLAN_TOPIC = import.meta.env.VITE_LOCAL_PLAN_TOPIC || '/local_plan';
const FOOTPRINT_TOPIC = import.meta.env.VITE_FOOTPRINT_TOPIC || '/local_costmap/published_footprint';

export default function NavMap({ ros, connected, autoMode, robotStarted }) {
  const rootRef = useRef(null); const readyRef = useRef(false);
  const [mapReady, setMapReady] = useState(false); const [goal, setGoal] = useState(null); const [navStatus, setNavStatus] = useState('Idle');

  useEffect(() => {
    if (!connected || !ros || !window.ROS2D || !window.createjs) return undefined;
    const root = rootRef.current; root.innerHTML = ''; readyRef.current = false; setMapReady(false);
    const viewer = new window.ROS2D.Viewer({ divID: root.id, width: root.clientWidth || 900, height: 600, background: '#101827' });
    const grid = new window.ROS2D.OccupancyGridClient({ ros, rootObject: viewer.scene, topic: MAP_TOPIC, continuous: true });
    grid.on('change', () => { viewer.scaleToDimensions(grid.currentGrid.width, grid.currentGrid.height); viewer.shift(grid.currentGrid.pose.position.x, grid.currentGrid.pose.position.y); readyRef.current = true; setMapReady(true); });

    const laser = new ROSLIB.Topic({ ros, name: SCAN_TOPIC, messageType: 'sensor_msgs/msg/LaserScan', throttle_rate: 100 });
    const scanShape = new window.createjs.Shape(); viewer.scene.addChild(scanShape);
    laser.subscribe((m) => { scanShape.graphics.clear().beginFill('#31d0aa'); for (let i=0;i<m.ranges.length;i+=3){const r=m.ranges[i];if(!Number.isFinite(r)||r<m.range_min||r>m.range_max)continue;const a=m.angle_min+i*m.angle_increment;scanShape.graphics.drawCircle(r*Math.cos(a),-r*Math.sin(a),0.015);} });

    const subscribePath = (name,color) => { const t=new ROSLIB.Topic({ros,name,messageType:'nav_msgs/msg/Path',throttle_rate:100}); const s=new window.createjs.Shape();viewer.scene.addChild(s);t.subscribe((m)=>{s.graphics.clear().setStrokeStyle(0.025).beginStroke(color);m.poses.forEach((p,i)=>i?s.graphics.lineTo(p.pose.position.x,-p.pose.position.y):s.graphics.moveTo(p.pose.position.x,-p.pose.position.y));});return t; };
    const globalPath=subscribePath(PLAN_TOPIC,'#4f8cff'); const localPath=subscribePath(LOCAL_PLAN_TOPIC,'#ffb84d');
    const footprint=new ROSLIB.Topic({ros,name:FOOTPRINT_TOPIC,messageType:'geometry_msgs/msg/PolygonStamped',throttle_rate:100}); const fs=new window.createjs.Shape();viewer.scene.addChild(fs);
    footprint.subscribe((m)=>{const pts=m.polygon.points||[];fs.graphics.clear().setStrokeStyle(0.03).beginStroke('#ff5d73');pts.forEach((p,i)=>i?fs.graphics.lineTo(p.x,-p.y):fs.graphics.moveTo(p.x,-p.y));if(pts.length)fs.graphics.lineTo(pts[0].x,-pts[0].y);});

    const goalTopic=new ROSLIB.Topic({ros,name:'/web_navigation/goal',messageType:'geometry_msgs/msg/PoseStamped'});
    const statusTopic=new ROSLIB.Topic({ros,name:'/web_navigation/status',messageType:'std_msgs/msg/String'}); statusTopic.subscribe((m)=>setNavStatus(m.data));
    const click=(event)=>{if(!autoMode||!robotStarted||!readyRef.current)return;const p=viewer.scene.globalToRos(event.stageX,event.stageY);setGoal({x:p.x,y:p.y});goalTopic.publish(new ROSLIB.Message({header:{frame_id:'map'},pose:{position:{x:p.x,y:p.y,z:0},orientation:{x:0,y:0,z:0,w:1}}}));};
    viewer.scene.addEventListener('stagemousedown',click);
    return()=>{laser.unsubscribe();globalPath.unsubscribe();localPath.unsubscribe();footprint.unsubscribe();statusTopic.unsubscribe();viewer.scene.removeAllEventListeners();root.innerHTML='';};
  }, [ros, connected, autoMode, robotStarted]);

  const cancelGoal=()=>{if(!ros)return;new ROSLIB.Topic({ros,name:'/cancel_navigation',messageType:'std_msgs/msg/Empty'}).publish(new ROSLIB.Message({}));setGoal(null);};
  return <Card className="panel-card h-100"><Card.Body><div className="d-flex justify-content-between align-items-center mb-2"><Card.Title className="mb-0">Nav2 Map</Card.Title><div className="d-flex gap-2"><Badge bg={mapReady?'success':'secondary'}>{mapReady?'Map ready':'Waiting map'}</Badge><Button size="sm" variant="outline-danger" onClick={cancelGoal}>Cancel goal</Button></div></div><div id="nav-map-root" ref={rootRef} className="nav-map"/><div className="d-flex justify-content-between mt-2"><small className="text-secondary">Auto + Started: click map to navigate {goal&&`· ${goal.x.toFixed(2)}, ${goal.y.toFixed(2)}`}</small><small>{navStatus}</small></div></Card.Body></Card>;
}
