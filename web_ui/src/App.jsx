import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, Button, ButtonGroup, Card, Col, Container, Form, Navbar, ProgressBar, Row } from 'react-bootstrap';
import ROSLIB from 'roslib';
import NavMap from './components/NavMap';

const DEFAULT_URL = import.meta.env.VITE_ROSBRIDGE_URL || 'ws://localhost:9090';
const TOPICS = {
  cmdVel: import.meta.env.VITE_CMD_VEL_TOPIC || '/cmd_vel', odom: import.meta.env.VITE_ODOM_TOPIC || '/odom',
  battery: import.meta.env.VITE_BATTERY_TOPIC || '/battery_state', estop: import.meta.env.VITE_ESTOP_TOPIC || '/emergency_stop',
  mode: import.meta.env.VITE_MODE_TOPIC || '/robot/mode', started: import.meta.env.VITE_STARTED_TOPIC || '/robot/started',
};

function App() {
  const [url, setUrl] = useState(DEFAULT_URL); const [connected, setConnected] = useState(false); const [status, setStatus] = useState('Disconnected');
  const [battery, setBattery] = useState({ percentage: 0, voltage: 0 }); const [odom, setOdom] = useState({ x: 0, y: 0, vx: 0, vy: 0, wz: 0 });
  const [estop, setEstop] = useState(false); const [speed, setSpeed] = useState(0.25); const [turnSpeed, setTurnSpeed] = useState(0.8);
  const [mode, setMode] = useState('manual'); const [started, setStarted] = useState(false);
  const rosRef = useRef(null); const cmdRef = useRef(null); const activeCommand = useRef({ x: 0, y: 0, z: 0 });

  const callTrigger = useCallback((name) => new Promise((resolve) => {
    if (!rosRef.current || !connected) return resolve({ success: false, message: 'ROS disconnected' });
    new ROSLIB.Service({ ros: rosRef.current, name, serviceType: 'std_srvs/srv/Trigger' }).callService(new ROSLIB.ServiceRequest({}), resolve);
  }), [connected]);
  const setRobotMode = useCallback((auto) => {
    if (!rosRef.current || !connected) return;
    const service = new ROSLIB.Service({ ros: rosRef.current, name: '/robot/set_auto_mode', serviceType: 'std_srvs/srv/SetBool' });
    service.callService(new ROSLIB.ServiceRequest({ data: auto }), (r) => r.success && setMode(auto ? 'auto' : 'manual'));
  }, [connected]);

  const publishVelocity = useCallback((x = 0, y = 0, z = 0) => {
    activeCommand.current = { x, y, z };
    if (!connected || !cmdRef.current || estop || !started || mode !== 'manual') return;
    cmdRef.current.publish(new ROSLIB.Message({ linear: { x, y, z: 0 }, angular: { x: 0, y: 0, z } }));
  }, [connected, estop, mode, started]);
  const stopMotion = useCallback(() => { activeCommand.current = { x: 0, y: 0, z: 0 }; if (cmdRef.current) cmdRef.current.publish(new ROSLIB.Message({ linear: { x: 0, y: 0, z: 0 }, angular: { x: 0, y: 0, z: 0 } })); }, []);

  const connect = useCallback(() => {
    rosRef.current?.close(); setStatus('Connecting'); const ros = new ROSLIB.Ros({ url }); rosRef.current = ros;
    ros.on('connection', () => { setConnected(true); setStatus('Connected'); cmdRef.current = new ROSLIB.Topic({ ros, name: TOPICS.cmdVel, messageType: 'geometry_msgs/msg/Twist' }); });
    ros.on('error', () => { setConnected(false); setStatus('Connection error'); }); ros.on('close', () => { setConnected(false); setStatus('Disconnected'); activeCommand.current = { x: 0, y: 0, z: 0 }; });
    new ROSLIB.Topic({ ros, name: TOPICS.odom, messageType: 'nav_msgs/msg/Odometry' }).subscribe((m) => setOdom({ x: m.pose.pose.position.x || 0, y: m.pose.pose.position.y || 0, vx: m.twist.twist.linear.x || 0, vy: m.twist.twist.linear.y || 0, wz: m.twist.twist.angular.z || 0 }));
    new ROSLIB.Topic({ ros, name: TOPICS.battery, messageType: 'sensor_msgs/msg/BatteryState' }).subscribe((m) => setBattery({ percentage: Number.isFinite(m.percentage) ? Math.max(0, Math.min(100, m.percentage * 100)) : 0, voltage: m.voltage || 0 }));
    new ROSLIB.Topic({ ros, name: TOPICS.estop, messageType: 'std_msgs/msg/Bool' }).subscribe((m) => { setEstop(Boolean(m.data)); if (m.data) stopMotion(); });
    new ROSLIB.Topic({ ros, name: TOPICS.mode, messageType: 'std_msgs/msg/String' }).subscribe((m) => setMode(m.data || 'manual'));
    new ROSLIB.Topic({ ros, name: TOPICS.started, messageType: 'std_msgs/msg/Bool' }).subscribe((m) => setStarted(Boolean(m.data)));
  }, [stopMotion, url]);

  useEffect(() => { connect(); return () => { stopMotion(); rosRef.current?.close(); }; }, []);
  useEffect(() => { const timer = setInterval(() => { const c = activeCommand.current; if (connected && !estop && started && mode === 'manual' && (c.x || c.y || c.z)) publishVelocity(c.x, c.y, c.z); }, 100); return () => clearInterval(timer); }, [connected, estop, mode, publishVelocity, started]);
  useEffect(() => { const map = { w: [speed,0,0], s:[-speed,0,0], a:[0,speed,0], d:[0,-speed,0], q:[0,0,turnSpeed], e:[0,0,-turnSpeed] }; const down=(e)=>{const c=map[e.key.toLowerCase()]; if(!e.repeat&&c){e.preventDefault();publishVelocity(...c);}}; const up=(e)=>map[e.key.toLowerCase()]&&stopMotion(); window.addEventListener('keydown',down); window.addEventListener('keyup',up); window.addEventListener('blur',stopMotion); return()=>{window.removeEventListener('keydown',down);window.removeEventListener('keyup',up);window.removeEventListener('blur',stopMotion);}; }, [publishVelocity,speed,stopMotion,turnSpeed]);

  const batteryVariant = useMemo(() => battery.percentage > 50 ? 'success' : battery.percentage > 20 ? 'warning' : 'danger', [battery]);
  const disabledManual = !connected || estop || !started || mode !== 'manual';
  const motionButton=(label,icon,x,y,z)=><Button className="motion-button" variant="outline-primary" disabled={disabledManual} onPointerDown={()=>publishVelocity(x,y,z)} onPointerUp={stopMotion} onPointerLeave={stopMotion} onPointerCancel={stopMotion}><i className={`bi ${icon}`}/> {label}</Button>;

  return <><Navbar className="app-navbar" data-bs-theme="dark"><Container fluid><Navbar.Brand><i className="bi bi-robot me-2"/>Moebius Nav2 Console</Navbar.Brand><div className="d-flex gap-2"><Badge bg={started?'success':'secondary'}>{started?'STARTED':'STOPPED'}</Badge><Badge bg={mode==='auto'?'warning':'primary'}>{mode.toUpperCase()}</Badge><Badge bg={connected?'success':'secondary'}>{status}</Badge></div></Container></Navbar>
  <Container fluid className="py-3">{estop&&<div className="alert alert-danger fw-bold">EMERGENCY STOP ACTIVE — all motion is blocked.</div>}
    <Row className="g-3 mb-3"><Col xl={3}><Card className="panel-card h-100"><Card.Body><Card.Title>Robot Control</Card.Title><Form.Control value={url} onChange={(e)=>setUrl(e.target.value)}/><Button className="w-100 mt-2" onClick={connect}>Connect</Button><hr/><div className="d-grid gap-2"><Button variant="success" disabled={!connected||started||estop} onClick={async()=>{const r=await callTrigger('/robot/start'); if(r.success)setStarted(true);}}>Start Robot</Button><Button variant="danger" disabled={!connected||!started} onClick={async()=>{stopMotion();const r=await callTrigger('/robot/stop');if(r.success)setStarted(false);}}>Stop Robot</Button><Button variant="warning" disabled={!connected} onClick={async()=>{stopMotion();await callTrigger('/robot/reset');}}>Reset Robot</Button></div><hr/><ButtonGroup className="w-100"><Button variant={mode==='manual'?'primary':'outline-primary'} onClick={()=>setRobotMode(false)}>Manual</Button><Button variant={mode==='auto'?'warning':'outline-warning'} disabled={!started||estop} onClick={()=>{stopMotion();setRobotMode(true);}}>Auto</Button></ButtonGroup><hr/><div className="metric"><span>Battery</span><strong>{battery.percentage.toFixed(0)}% · {battery.voltage.toFixed(2)} V</strong></div><ProgressBar now={battery.percentage} variant={batteryVariant}/></Card.Body></Card></Col>
    <Col xl={6}><NavMap ros={rosRef.current} connected={connected} autoMode={mode==='auto'} robotStarted={started}/></Col>
    <Col xl={3}><Card className="panel-card h-100"><Card.Body><Card.Title>Mecanum Manual</Card.Title><div className="teleop-grid">{motionButton('Rotate L','bi-arrow-counterclockwise',0,0,turnSpeed)}{motionButton('Forward','bi-arrow-up',speed,0,0)}{motionButton('Rotate R','bi-arrow-clockwise',0,0,-turnSpeed)}{motionButton('Left','bi-arrow-left',0,speed,0)}<Button variant="danger" className="motion-button" onClick={stopMotion}>STOP</Button>{motionButton('Right','bi-arrow-right',0,-speed,0)}<span/>{motionButton('Reverse','bi-arrow-down',-speed,0,0)}<span/></div><Form.Label className="mt-3">Linear {speed.toFixed(2)} m/s</Form.Label><Form.Range min="0.05" max="0.7" step="0.05" value={speed} onChange={(e)=>setSpeed(Number(e.target.value))}/><Form.Label>Turn {turnSpeed.toFixed(1)} rad/s</Form.Label><Form.Range min="0.2" max="3" step="0.1" value={turnSpeed} onChange={(e)=>setTurnSpeed(Number(e.target.value))}/><hr/>{[['X',odom.x,'m'],['Y',odom.y,'m'],['Vx',odom.vx,'m/s'],['Vy',odom.vy,'m/s'],['Wz',odom.wz,'rad/s']].map(([n,v,u])=><div className="metric" key={n}><span>{n}</span><strong>{v.toFixed(3)} {u}</strong></div>)}</Card.Body></Card></Col></Row>
  </Container></>;
}
export default App;
