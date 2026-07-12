import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, Button, Card, Col, Container, Form, Navbar, ProgressBar, Row } from 'react-bootstrap';
import ROSLIB from 'roslib';

const DEFAULT_URL = import.meta.env.VITE_ROSBRIDGE_URL || 'ws://localhost:9090';
const TOPICS = {
  cmdVel: import.meta.env.VITE_CMD_VEL_TOPIC || '/cmd_vel',
  odom: import.meta.env.VITE_ODOM_TOPIC || '/odom',
  battery: import.meta.env.VITE_BATTERY_TOPIC || '/battery_state',
  estop: import.meta.env.VITE_ESTOP_TOPIC || '/emergency_stop',
};

function App() {
  const [url, setUrl] = useState(DEFAULT_URL);
  const [connected, setConnected] = useState(false);
  const [status, setStatus] = useState('Disconnected');
  const [battery, setBattery] = useState({ percentage: 0, voltage: 0 });
  const [odom, setOdom] = useState({ x: 0, y: 0, vx: 0, vy: 0, wz: 0 });
  const [estop, setEstop] = useState(false);
  const [speed, setSpeed] = useState(0.25);
  const [turnSpeed, setTurnSpeed] = useState(0.8);
  const rosRef = useRef(null);
  const cmdRef = useRef(null);
  const activeCommand = useRef({ x: 0, y: 0, z: 0 });

  const publishVelocity = useCallback((x = 0, y = 0, z = 0) => {
    activeCommand.current = { x, y, z };
    if (!connected || !cmdRef.current || estop) return;
    cmdRef.current.publish(new ROSLIB.Message({
      linear: { x, y, z: 0 },
      angular: { x: 0, y: 0, z },
    }));
  }, [connected, estop]);

  const stop = useCallback(() => publishVelocity(0, 0, 0), [publishVelocity]);

  const connect = useCallback(() => {
    if (rosRef.current) rosRef.current.close();
    setStatus('Connecting');
    const ros = new ROSLIB.Ros({ url });
    rosRef.current = ros;

    ros.on('connection', () => {
      setConnected(true);
      setStatus('Connected');
      cmdRef.current = new ROSLIB.Topic({ ros, name: TOPICS.cmdVel, messageType: 'geometry_msgs/msg/Twist' });
    });
    ros.on('error', (error) => {
      console.error(error);
      setConnected(false);
      setStatus('Connection error');
    });
    ros.on('close', () => {
      setConnected(false);
      setStatus('Disconnected');
      activeCommand.current = { x: 0, y: 0, z: 0 };
    });

    const odomTopic = new ROSLIB.Topic({ ros, name: TOPICS.odom, messageType: 'nav_msgs/msg/Odometry' });
    const batteryTopic = new ROSLIB.Topic({ ros, name: TOPICS.battery, messageType: 'sensor_msgs/msg/BatteryState' });
    const estopTopic = new ROSLIB.Topic({ ros, name: TOPICS.estop, messageType: 'std_msgs/msg/Bool' });

    odomTopic.subscribe((msg) => setOdom({
      x: msg.pose.pose.position.x || 0,
      y: msg.pose.pose.position.y || 0,
      vx: msg.twist.twist.linear.x || 0,
      vy: msg.twist.twist.linear.y || 0,
      wz: msg.twist.twist.angular.z || 0,
    }));
    batteryTopic.subscribe((msg) => setBattery({
      percentage: Number.isFinite(msg.percentage) ? Math.max(0, Math.min(100, msg.percentage * 100)) : 0,
      voltage: msg.voltage || 0,
    }));
    estopTopic.subscribe((msg) => {
      setEstop(Boolean(msg.data));
      if (msg.data) stop();
    });
  }, [stop, url]);

  useEffect(() => {
    connect();
    return () => {
      stop();
      rosRef.current?.close();
    };
  }, []); // Connect once on startup.

  useEffect(() => {
    const timer = window.setInterval(() => {
      const { x, y, z } = activeCommand.current;
      if (connected && !estop && (x || y || z)) publishVelocity(x, y, z);
    }, 100);
    return () => window.clearInterval(timer);
  }, [connected, estop, publishVelocity]);

  useEffect(() => {
    const keyMap = {
      w: [speed, 0, 0], s: [-speed, 0, 0],
      a: [0, speed, 0], d: [0, -speed, 0],
      q: [0, 0, turnSpeed], e: [0, 0, -turnSpeed],
    };
    const down = (event) => {
      if (event.repeat || !keyMap[event.key.toLowerCase()]) return;
      event.preventDefault();
      publishVelocity(...keyMap[event.key.toLowerCase()]);
    };
    const up = (event) => {
      if (keyMap[event.key.toLowerCase()]) stop();
    };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', stop);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', stop);
    };
  }, [publishVelocity, speed, stop, turnSpeed]);

  const batteryVariant = useMemo(() => battery.percentage > 50 ? 'success' : battery.percentage > 20 ? 'warning' : 'danger', [battery]);
  const motionButton = (label, icon, x, y, z) => (
    <Button className="motion-button" variant="outline-primary"
      disabled={!connected || estop}
      onPointerDown={() => publishVelocity(x, y, z)}
      onPointerUp={stop} onPointerLeave={stop} onPointerCancel={stop}>
      <i className={`bi ${icon}`} /> <span>{label}</span>
    </Button>
  );

  return <>
    <Navbar className="app-navbar" data-bs-theme="dark">
      <Container fluid>
        <Navbar.Brand><i className="bi bi-robot me-2" />Moebius Robot</Navbar.Brand>
        <Badge bg={connected ? 'success' : 'secondary'}>{status}</Badge>
      </Container>
    </Navbar>
    <Container fluid className="py-3">
      {estop && <div className="alert alert-danger fw-bold">EMERGENCY STOP ACTIVE — motion commands are blocked.</div>}
      <Row className="g-3">
        <Col xl={4}>
          <Card className="h-100 panel-card"><Card.Body>
            <Card.Title>ROS Bridge</Card.Title>
            <Form.Label>WebSocket URL</Form.Label>
            <div className="d-flex gap-2">
              <Form.Control value={url} onChange={(e) => setUrl(e.target.value)} />
              <Button onClick={connect}>Connect</Button>
            </div>
            <small className="text-secondary">Typical: ws://ROBOT_IP:9090</small>
            <hr />
            <div className="metric"><span>Battery</span><strong>{battery.percentage.toFixed(0)}% · {battery.voltage.toFixed(2)} V</strong></div>
            <ProgressBar now={battery.percentage} variant={batteryVariant} className="mb-3" />
            <div className="metric"><span>E-stop</span><Badge bg={estop ? 'danger' : 'success'}>{estop ? 'ACTIVE' : 'OK'}</Badge></div>
          </Card.Body></Card>
        </Col>
        <Col xl={4}>
          <Card className="h-100 panel-card"><Card.Body>
            <Card.Title>Mecanum Teleop</Card.Title>
            <div className="teleop-grid">
              {motionButton('Rotate L', 'bi-arrow-counterclockwise', 0, 0, turnSpeed)}
              {motionButton('Forward', 'bi-arrow-up', speed, 0, 0)}
              {motionButton('Rotate R', 'bi-arrow-clockwise', 0, 0, -turnSpeed)}
              {motionButton('Left', 'bi-arrow-left', 0, speed, 0)}
              <Button variant="danger" className="motion-button" onClick={stop}><i className="bi bi-stop-fill" /> STOP</Button>
              {motionButton('Right', 'bi-arrow-right', 0, -speed, 0)}
              <span />
              {motionButton('Reverse', 'bi-arrow-down', -speed, 0, 0)}
              <span />
            </div>
            <small className="text-secondary d-block mt-2">Keyboard: W/S forward, A/D strafe, Q/E rotate. Releasing a key sends zero velocity.</small>
            <Row className="mt-3 g-2">
              <Col><Form.Label>Linear {speed.toFixed(2)} m/s</Form.Label><Form.Range min="0.05" max="0.7" step="0.05" value={speed} onChange={(e) => setSpeed(Number(e.target.value))} /></Col>
              <Col><Form.Label>Turn {turnSpeed.toFixed(1)} rad/s</Form.Label><Form.Range min="0.2" max="3" step="0.1" value={turnSpeed} onChange={(e) => setTurnSpeed(Number(e.target.value))} /></Col>
            </Row>
          </Card.Body></Card>
        </Col>
        <Col xl={4}>
          <Card className="h-100 panel-card"><Card.Body>
            <Card.Title>Odometry</Card.Title>
            {[['X', odom.x, 'm'], ['Y', odom.y, 'm'], ['Vx', odom.vx, 'm/s'], ['Vy', odom.vy, 'm/s'], ['Wz', odom.wz, 'rad/s']].map(([name, value, unit]) =>
              <div className="metric" key={name}><span>{name}</span><strong>{value.toFixed(3)} {unit}</strong></div>)}
          </Card.Body></Card>
        </Col>
      </Row>
    </Container>
  </>;
}

export default App;
