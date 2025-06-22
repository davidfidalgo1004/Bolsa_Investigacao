import React from 'react';

export default function Sidebar({ open, onClose, controls }) {
  // controls: { iter, setIter, windSpeed, setWindSpeed, ... }
  const {
    iter, setIter,
    density, setDensity,
    windSpeed, setWindSpeed,
    windDir, setWindDir,
    precip, setPrecip,
    humid, setHumid,
    temp, setTemp,
    ffCount, setFfCount,
    ffRatio, setFfRatio,
    envType, setEnvType,
    mode, setMode,
    regionJson,
    setRegionJson,
    onCalcRisk,
  } = controls;

  const apiMode = mode === 'api';

  return (
    <div className={`sidebar ${open ? 'open' : ''}`}> 
      <button className="sidebar-close" onClick={onClose}>×</button>
      <h3>Parâmetros</h3>
      <div className="sidebar-group">
        <label>Iterações: {iter}
          <input type="range" min="10" max="500" value={iter} onChange={e=>setIter(+e.target.value)} disabled={apiMode} />
        </label>
        <label>Densidade: {density}%
          <input type="range" min="0" max="100" value={density} onChange={e=>setDensity(+e.target.value)} disabled={apiMode} />
        </label>
        <label>Temperatura: {temp}°C
          <input type="range" min="0" max="40" value={temp} onChange={e=>setTemp(+e.target.value)} disabled={apiMode} />
        </label>
        <label>Humidade: {humid}%
          <input type="range" min="0" max="100" value={humid} onChange={e=>setHumid(+e.target.value)} disabled={apiMode} />
        </label>
        <label>Precipitação: {precip}%
          <input type="range" min="0" max="100" value={precip} onChange={e=>setPrecip(+e.target.value)} disabled={apiMode} />
        </label>
        <label>Vento (m/s): {windSpeed}
          <input type="range" min="0" max="15" value={windSpeed} onChange={e=>setWindSpeed(+e.target.value)} disabled={apiMode} />
        </label>
        <label>Direção Vento: {windDir}°
          <input type="range" min="0" max="359" value={windDir} onChange={e=>setWindDir(+e.target.value)} disabled={apiMode} />
        </label>
        <hr />
        <label>Bombeiros Nº: {ffCount}
          <input type="range" min="4" max="120" value={ffCount} onChange={e=>setFfCount(+e.target.value)} />
        </label>
        <label>Ratio Tec|Água: {ffRatio}%
          <input type="range" min="0" max="100" value={ffRatio} onChange={e=>setFfRatio(+e.target.value)} disabled={apiMode} />
        </label>
        <hr />
        <div>
          <p>Ambiente:</p>
          <label><input type="radio" checked={envType==='only_trees'} onChange={()=>setEnvType('only_trees')} disabled={apiMode}/> Árvores</label><br />
          <label><input type="radio" checked={envType==='road_trees'} onChange={()=>setEnvType('road_trees')} disabled={apiMode}/> Estrada+Árvores</label><br />
          <label><input type="radio" checked={envType==='river_trees'} onChange={()=>setEnvType('river_trees')} disabled={apiMode}/> Rio+Árvores</label>
        </div>
        <div>
          <p>Modo:</p>
          <label><input type="radio" checked={mode==='sim'} onChange={()=>setMode('sim')} /> Simulado</label><br />
          <label><input type="radio" checked={mode==='api'} onChange={()=>setMode('api')} /> Real (API)</label>
        </div>
        <hr />
        <div>
          <p><strong>GeoJSON Área</strong></p>
          <input type="file" accept=".geojson,application/json" disabled={!apiMode}
          onChange={e=>{
            const file=e.target.files[0];
            if(!file)return;
            const reader=new FileReader();
            reader.onload=ev=>{
              try{setRegionJson(JSON.parse(ev.target.result));}
              catch(err){alert('Ficheiro GeoJSON inválido');}
            };
            reader.readAsText(file);
          }} />
          <button onClick={onCalcRisk} disabled={!regionJson || !apiMode}>Calcular Risco</button>
        </div>
      </div>
    </div>
  );
} 