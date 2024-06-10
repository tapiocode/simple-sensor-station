/**
 * Copyright (c) 2024 tapiocode
 * https://github.com/tapiocode
 * MIT License
 */

import { getCurrentReading, getSensors } from './reader.js';

dayjs.extend(window.dayjs_plugin_relativeTime);
dayjs.extend(window.dayjs_plugin_duration);

const SESSION_STORAGE_SELECTED_MAC = 'selectedMac'

const sensorSelect = document.getElementById('sensors');
sensorSelect.addEventListener('change', (event) => {
    setSelectedMac(event.target.value);
    updateAll();
});
const errors = [];

setInterval(() => updateAll(), 5000);
updateAll();

async function updateAll() {
    const sensorsError = 'Failed to fetch sensors';
    const sensors = await getSensors(setError(sensorsError));
    if (sensors) {
        updateSensors(sensors);
        clearError(sensorsError);
    }

    const selectedMac = sessionStorage.getItem(SESSION_STORAGE_SELECTED_MAC);
    if (selectedMac) {
        const readingError = 'Failed to fetch readings';
        const reading = await getCurrentReading(selectedMac, setError(readingError));
        if (reading) {
            updateReading(reading);
            clearError(readingError);
        }
    }
}

function setError(errorMsg) {
    return () => {
        console.error(errorMsg);
        if (!errors.includes(errorMsg)) {
            errors.push(errorMsg);
            updateErrors();
        }
    };
}

function clearError(errorMsg) {
    if (errors.includes(errorMsg)) {
        errors.splice(errors.indexOf(errorMsg), 1);
        updateErrors();
    }
}

function updateErrors() {
    const errorsContainer = document.getElementById('errors');
    errorsContainer.innerHTML = '';
    errors.forEach((err) => {
        errorsContainer.insertAdjacentHTML('beforeend', `<li>${err}</li>`);
    });
}

function updateSensors(sensors) {
    sensorSelect.innerHTML = '';
    setHtml('selectedSensorName', '–');
    if (sensors.length > 0) {
        const selectedSensor = getSelectedSensorStored(sensors);
        setHtml('selectedSensorName', selectedSensor.name);
        sensors.forEach((sensor) =>
            sensorSelect.appendChild(getRadio(sensor, selectedSensor.mac)));
    } else {
        sensorSelect.innerHTML = 'No sensors';
    }
}

function updateReading(reading) {
    const DEGREE = '&#176;';
    const now = new Date();
    const ago = new Date(reading.timestamp);
    const diffSeconds = (ago - now) / 1000;
    const timeAgoText = dayjs.duration(diffSeconds, 'seconds').humanize(true);
    setHtml('timeAgo', timeAgoText);
    setHtml('temperature', getDecimalStr(reading.temperature));
    setHtml('humidity', Math.round(reading.humidity));
    setHtml('pressure', getDecimalStr(reading.pressure));
    setHtml('unit', ` ${DEGREE}C`);
    document.querySelector('.secondary-info').classList.remove('hidden');
    document.title = `${reading.temperature} C`;
}

function getDecimalStr(float) {
    const integer = Math.floor(float);
    const decimals = ((float * 100) % 100).toString().padStart(2, '0');
    return `${integer}.${decimals}`;
}

function setSelectedMac(mac) {
    sessionStorage.setItem(SESSION_STORAGE_SELECTED_MAC, mac);
}

function getSelectedSensorStored(sensors) {
    const storedMac = sessionStorage.getItem(SESSION_STORAGE_SELECTED_MAC);
    if (storedMac) {
        const storedSensor = sensors.find((sensor) => sensor.mac === storedMac);
        if (storedSensor) {
            return storedSensor;
        }
        sessionStorage.removeItem(SESSION_STORAGE_SELECTED_MAC);
    }
    setSelectedMac(sensors[0].mac);
    return sensors[0];
}

function getRadio(sensor, selectedMac) {
    const row = document.getElementById('sensorRow').content.cloneNode(true);
    row.querySelector('[data-name]').innerHTML = resolveSensorName(sensor);
    if (!sensor.name) {
        row.querySelector('[data-name]').classList.add('monospace');
    }
    row.querySelector('[data-mac]').innerHTML = sensor.mac;
    row.querySelector('input').value = sensor.mac;
    row.querySelector('input').checked = sensor.mac === selectedMac;
    row.querySelector('button').addEventListener('click', () => editSensor(sensor.mac, sensor.name));
    return row;
}

function setHtml(id, html) {
    document.getElementById(id).innerHTML = html;
}

function editSensor(mac, name) {
    const newName = prompt('Edit name:', name);
    if (newName !== null) {
        fetch(`/api/sensors`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mac, name: newName }),
        })
            .then((response) => {
                if (response.ok) {
                    updateAll();
                } else {
                    alert('Failed to update sensor');
                }
            })
            .catch((err) => {
                console.error(err);
                alert('Failed to update sensor');
            });
    }
}

function resolveSensorName(sensor) {
    return sensor.name || 'RuuviTag';
}
