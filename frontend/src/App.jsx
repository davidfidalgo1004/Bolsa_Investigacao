import React, { useEffect, useRef, useState } from 'react';
// 🚫 Deixamos de usar MapLibre – grid apenas
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';
import './app.css';
import Sidebar from './Sidebar.jsx';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WORLD_W = 125;
const WORLD_H = 108;

// Helper http→ws
const httpToWs = (url) => {
  const u = new URL(url);
  u.protocol = u.protocol.replace('http', 'ws');
  return u.toString().replace(/\/$/, '') + '/ws';
};

// Helper to push log messages
function useLogs() {
  const [logs, setLogs] = useState(['Interface pronta. Ajuste as configurações e clique em "Setup".']);
  const addLog = (msg) => setLogs((prev) => [...prev, msg]);
  return { logs, addLog };
}

export default function App() {
  const { logs, addLog } = useLogs();
  const imgRef = useRef(null);
  const wsRef = useRef(null);

  // ------------------ Control states ------------------
  const [iter, setIter] = useState(100);
  const [envType, setEnvType] = useState('only_trees');
  const [mode, setMode] = useState('sim');
  const [windSpeed, setWindSpeed] = useState(4);
  const [windDir, setWindDir] = useState(0);
  const [density, setDensity] = useState(50);
  const [precip, setPrecip] = useState(50);
  const [humid, setHumid] = useState(15);
  const [temp, setTemp] = useState(25);
  const [ffCount, setFfCount] = useState(4);
  const [ffRatio, setFfRatio] = useState(50);

  const [burnData, setBurnData] = useState([]);
  const [airData,setAirData]=useState([]); // {tick,co,co2,pm25,pm10,o2}
  const [climateData,setClimateData]=useState([]); // {tick,temp,humid,precip}
  const [ffData,setFfData]=useState([]);
  const [running, setRunning] = useState(false);
  const [imgUrl, setImgUrl] = useState(null);
  const [bounds, setBounds] = useState([-9.56, -6.18, 36.96, 42.18]); // default PT
  const [stats, setStats] = useState({});
  const [regionJson, setRegionJson] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // chart selection state
  const [chartTab,setChartTab]=useState('fire');

  // ---------------- WebSocket ----------------
  const connectWS = () => {
    if (wsRef.current) wsRef.current.close();
    const ws = new WebSocket(httpToWs(API_BASE));
    wsRef.current = ws;

    ws.onopen = () => console.log('[WS] conectado');

    ws.onmessage = (evt) => {
      const data = JSON.parse(evt.data);
      setBurnData((prev) => [...prev, { tick: data.tick, burned: data.burned, forested: data.forested }]);
      if (data.img) setImgUrl(data.img);
      if (data.bounds) setBounds(data.bounds);
      if (data.stats) setStats(data.stats);
      if(data.stats?.pollutants){
        const p=data.stats.pollutants;
        setAirData(prev=>[...prev,{tick:data.tick,...p}]);
      }
      if(data.stats?.ff_evo){ setFfData(prev=>[...prev,data.stats.ff_evo]); }
      setClimateData(prev=>[...prev,{tick:data.tick,temp:data.stats?.temperature,humid:data.stats?.humidity,precip:data.stats?.precipitation}]);
      addLog(`Iteração ${data.tick} | Queimadas: ${data.burned}, Florestadas: ${data.forested}`);
    };

    ws.onclose = () => {
      console.log('[WS] fechado');
      setRunning(false);
    };
  };

  // ---------------- Handlers ----------------
  const handleSetup = async () => {
    try {
      const resp = await axios.post(`${API_BASE}/setup`, { density: density / 100 });
      if (resp.data?.bounds) setBounds(resp.data.bounds);
      if (resp.data?.img) setImgUrl(resp.data.img);
      if (resp.data) {
        setBurnData([{ tick: 0, burned: resp.data.burned ?? 0, forested: resp.data.forested ?? 0 }]);
        if(resp.data.pollutants){
          const p=resp.data.pollutants;
          setAirData([{tick:0,...p}]);
        }
        if(resp.data.ff_evo){ setFfData([resp.data.ff_evo]); }
        setClimateData([{tick:0,temp:resp.data.temperature,humid:resp.data.humidity,precip:resp.data.precipitation}]);
      }
      addLog('Modelo criado / cenário pronto.');
    } catch (err) {
      console.error(err);
      alert('Erro no setup');
    }
  };

  const handleStart = async () => {
    try {
      await axios.post(`${API_BASE}/start`);
      connectWS();
      setRunning(true);
      addLog('Simulação iniciada');
    } catch (err) {
      console.error(err);
    }
  };

  const handlePause = async () => {
    try {
      await axios.post(`${API_BASE}/pause`);
      if (wsRef.current) wsRef.current.close();
      addLog('Simulação pausada');
    } catch (err) {
      console.error(err);
    }
  };

  const handleStep = async () => {
    try {
      const resp = await axios.post(`${API_BASE}/step`);
      if (resp.data?.img) {
        setImgUrl(resp.data.img);
      } else {
        // fallback: pede 1 step para obter imagem inicial (tick 0)
        try {
          const s = await axios.post(`${API_BASE}/step`);
          if (s.data?.img) setImgUrl(s.data.img);
        } catch {}
      }
      if (resp.data?.bounds) setBounds(resp.data.bounds);
      if (resp.data) {
        setBurnData((prev)=>[...prev,{tick:resp.data.tick,burned:resp.data.burned,forested:resp.data.forested}]);
        addLog(`(Step) Iteração ${resp.data.tick}`);
      }
    } catch(err){console.error(err);}
  };

  // ----- Risk via API -----
  const handleCalcRisk = async () => {
    if(!regionJson){alert('Carregue um GeoJSON primeiro');return;}
    try {
      const resp = await axios.post(`${API_BASE}/region`, regionJson);
      if(resp.data?.bounds) setBounds(resp.data.bounds);
      const riskResp = await axios.post(`${API_BASE}/risk`, regionJson);
      addLog('Risco calculado com sucesso');
      // Extrair valores médios
      const feats = Array.isArray(riskResp.data?.features)?riskResp.data.features:[];
      let tempSum=0,humSum=0,precSum=0,windS=0,windD=0,count=0;
      feats.forEach(f=>{
        const p=f.properties||{};
        if(p.temperature!=null){tempSum+=p.temperature;}
        if(p.humidity!=null){humSum+=p.humidity;}
        if(p.precipitation!=null){precSum+=p.precipitation*100;}
        if(p.wind_speed!=null){windS+=p.wind_speed;}
        if(p.wind_direction!=null){windD+=p.wind_direction;}
        count++;
      });
      if(count){
        if(tempSum) setTemp(Math.round(tempSum/count));
        if(humSum) setHumid(Math.round(humSum/count));
        if(precSum) setPrecip(Math.round(precSum/count));
        if(windS) setWindSpeed(Math.round(windS/count));
        if(windD) setWindDir(Math.round((windD/count)%360));
        addLog('Sliders actualizados com dados da API');
      }
    } catch(err){console.error(err);addLog('Erro ao calcular risco');}
  };

  // Ignite on click
  const handleImgClick = async (e) => {
    if (!imgRef.current) return;
    const rect = imgRef.current.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;

    const cellW = rect.width / WORLD_W;
    const cellH = rect.height / WORLD_H;
    const gx = Math.floor(px / cellW);
    const gy = Math.floor(py / cellH);

    // Converte grid → lat/lon (inverso de backend)
    const [lonMin, lonMax, latMin, latMax] = bounds;
    const lonSpan = lonMax - lonMin;
    const latSpan = latMax - latMin;
    const lon = lonMin + (gx / (WORLD_W - 1)) * lonSpan;
    const lat = latMax - (gy / (WORLD_H - 1)) * latSpan;

    try {
      await axios.post(`${API_BASE}/ignite`, { lat, lon });
      addLog(`Ignição em lon ${lon.toFixed(4)}, lat ${lat.toFixed(4)}`);
    } catch (err) {
      console.error('Ignite error', err);
    }
  };

  // ---------------- Render ----------------
  return (
    <div className="app-container">
      {/* ---------- Control Bar ---------- */}
      <div className="control-bar">
        <label>Iterações:
          <input type="range" min="10" max="500" value={iter} onChange={(e)=>setIter(Number(e.target.value))}/>
        </label>
        {/* Env radio */}
        <label><input type="radio" checked={envType==='only_trees'} onChange={()=>setEnvType('only_trees')} /> Somente Árvores</label>
        <label><input type="radio" checked={envType==='road_trees'} onChange={()=>setEnvType('road_trees')} /> Estrada + Árvores</label>
        <label><input type="radio" checked={envType==='river_trees'} onChange={()=>setEnvType('river_trees')} /> Rio + Árvores</label>
        {/* Mode radio */}
        <label><input type="radio" checked={mode==='sim'} onChange={()=>setMode('sim')} /> Modo Simulado</label>
        <label><input type="radio" checked={mode==='api'} onChange={()=>setMode('api')} /> Modo Real (API)</label>

        <button onClick={handleSetup}>Setup</button>
        <button onClick={handleStart} disabled={running}>Iniciar Simulação</button>
        <button onClick={handlePause} disabled={!running}>Pausar</button>
        <button onClick={handleStep}>Próximo Passo</button>
        <button onClick={()=>setSidebarOpen(o=>!o)}>⚙️</button>
      </div>

      {/* ---------- Main content ---------- */}
      <div className="main-content">
        {/* Left column */}
        <div className="left-pane">
          <textarea className="log-area" readOnly value={logs.join('\n')} />
          {/* Stats placeholder */}
          <div className="stats-pane">
            <p><strong>Temp:</strong> {stats.temperature?.toFixed?.(1) ?? '--'} °C | <strong>Hum:</strong> {stats.humidity?.toFixed?.(1) ?? '--'} %</p>
            <p><strong>Vento:</strong> {stats.wind_speed?.toFixed?.(1) ?? '--'} m/s @ {stats.wind_direction?.toFixed?.(0) ?? '--'}°</p>
            {stats.firefighters && (
              <p><strong>Bombeiros</strong> – Water {stats.firefighters.water ?? 0} | Tech {stats.firefighters.alternative ?? 0} | Ataque {stats.firefighters.direct_attack ?? 0} | Movendo {stats.firefighters.navigating ?? 0} | Ociosos {stats.firefighters.idle ?? 0}</p>
            )}
          </div>
        </div>

        {/* Grid image */}
        <div className="grid-pane">
          {imgUrl ? (
            <img
              ref={imgRef}
              src={imgUrl}
              alt="grid"
              className="grid-image"
              onClick={handleImgClick}
            />
          ) : (
            <span style={{ color: '#ddd' }}>Sem imagem (execute Setup & Iniciar)</span>
          )}
        </div>
      </div>

      {/* ---------- Graph ---------- */}
      <div className="graph-pane">
        <div style={{marginBottom:'6px'}}>
          <button onClick={()=>setChartTab('monitor')} disabled={chartTab==='monitor'}>Monitor</button>
          <button onClick={()=>setChartTab('fire')} disabled={chartTab==='fire'}>Incêndio</button>
          <button onClick={()=>setChartTab('air')} disabled={chartTab==='air'}>Qualidade Ar</button>
          <button onClick={()=>setChartTab('climate')} disabled={chartTab==='climate'}>Clima</button>
          <button onClick={()=>setChartTab('ff')} disabled={chartTab==='ff'}>Bombeiros</button>
        </div>
        {chartTab==='monitor' && (
          <div style={{display:'flex',gap:'20px',flexWrap:'wrap',color:'#9acd32'}}>
            <div className="compass">
              <div className="compass-arrow" style={{transform:`translateX(-50%) rotate(${stats.wind_direction ?? 0}deg)`}} />
            </div>
            <div className="monitor-pane" style={{border:'none'}}>
              <div><span>Temp:</span> {stats.temperature?.toFixed?.(1) ?? '--'} °C</div>
              <div><span>Humidade:</span> {stats.humidity?.toFixed?.(1) ?? '--'} %</div>
              <div><span>Precip.:</span> {stats.precipitation!=null ? (stats.precipitation*100).toFixed(0) : '--'} %</div>
              <div><span>Vento:</span> {stats.wind_speed?.toFixed?.(1) ?? '--'} m/s @ {stats.wind_direction?.toFixed?.(0) ?? '--'}°</div>
              {stats.pollutants && (
                <>
                  <div><span>CO:</span> {stats.pollutants.co?.toFixed?.(2) ?? '--'} ppm</div>
                  <div><span>CO₂:</span> {stats.pollutants.co2?.toFixed?.(2) ?? '--'} ppm</div>
                  <div><span>PM2.5:</span> {stats.pollutants.pm25?.toFixed?.(1) ?? '--'} µg/m³</div>
                  <div><span>PM10:</span> {stats.pollutants.pm10?.toFixed?.(1) ?? '--'} µg/m³</div>
                  <div><span>O₂:</span> {stats.pollutants.o2?.toFixed?.(2) ?? '--'} ppm</div>
                </>
              )}
            </div>
          </div>) }
        {chartTab==='fire' && (
          <LineChart width={600} height={200} data={burnData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tick" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="burned" stroke="#ff4500" name="Queimadas" />
            <Line type="monotone" dataKey="forested" stroke="#228B22" name="Florestadas" />
          </LineChart>) }
        {chartTab==='air' && (
          <LineChart width={600} height={200} data={airData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tick" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="co" stroke="#ff00ff" name="CO (ppm)" />
            <Line type="monotone" dataKey="co2" stroke="#00ffff" name="CO₂ (ppm)" />
            <Line type="monotone" dataKey="pm25" stroke="#ffa500" name="PM2.5" />
            <Line type="monotone" dataKey="pm10" stroke="#9370db" name="PM10" />
            <Line type="monotone" dataKey="o2" stroke="#00ff00" name="O₂ (ppm)" />
          </LineChart>) }
        {chartTab==='climate' && (
          <LineChart width={600} height={200} data={climateData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tick" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="temp" stroke="#ff0000" name="Temperatura (°C)" />
            <Line type="monotone" dataKey="humid" stroke="#1e90ff" name="Humidade (%)" />
            <Line type="monotone" dataKey="precip" stroke="#2e8b57" name="Precipitação (%)" />
          </LineChart>) }
        {chartTab==='ff' && (
          <LineChart width={600} height={200} data={ffData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="tick" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line dataKey="attack" stroke="#ff4500" name="Ataque" />
            <Line dataKey="firebreak" stroke="#ffa500" name="Firebreak" />
            <Line dataKey="moving" stroke="#00bfff" name="Movendo" />
            <Line dataKey="idle" stroke="#cccccc" name="Ociosos" />
          </LineChart>)}
      </div>

      {/* Sidebar Drawer */}
      <Sidebar open={sidebarOpen} onClose={()=>setSidebarOpen(false)} controls={{iter,setIter,density,setDensity,windSpeed,setWindSpeed,windDir,setWindDir,precip,setPrecip,humid,setHumid,temp,setTemp,ffCount,setFfCount,ffRatio,setFfRatio,envType,setEnvType,mode,setMode,regionJson,setRegionJson,onCalcRisk:handleCalcRisk}} />
    </div>
  );
} 