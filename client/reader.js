/**
 * Copyright (c) 2024 tapiocode
 * https://github.com/tapiocode
 * MIT License
 */

export async function getSensors(errorFn) {
  blinkIndicator();
  const sensors = await fetchData('/api/sensors').catch(
    () => errorFn('Failed to fetch sensors'));
  return sensors;
}

export async function getCurrentReading(mac, errorFn) {
  const readings = await fetchData(`/api/sensordata/${mac}`).catch(
    () => errorFn('Failed to fetch readings'));
  if (readings && readings.success) {
    const latest = readings.data[0];
    if (latest) {
      return latest;
    }
  }
  return null;
}

function blinkIndicator() {
  const indicator = document.querySelector('[data-sensor-updating]');
  indicator.style.opacity = '1';
  setTimeout(() => indicator.style.opacity = '0', 500);
}

function fetchData(url) {
  return fetch(url).then(res => res.json());
}
