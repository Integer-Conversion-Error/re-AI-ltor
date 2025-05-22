// Initialize the map
var mymap = L.map('mapid').setView([51.505, -0.09], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(mymap);

var drawnItems = new L.FeatureGroup();
mymap.addLayer(drawnItems);

var drawControl = new L.Control.Draw({
    edit: {
        featureGroup: drawnItems
    },
    draw: {
        polygon: true,
        polyline: false,
        rectangle: false,
        circle: false,
        marker: false,
        circlemarker: false
    }
});
mymap.addControl(drawControl);

var savedShapes = []; // Array to store all drawn shapes
var activeShapeId = null; // To keep track of the currently selected shape for editing/displaying results

// Get slider, value display, shape name input, and tab elements
const rectangleCountSlider = document.getElementById('rectangle-count');
const rectangleCountValueSpan = document.getElementById('rectangle-count-value');
const shapeNameInput = document.getElementById('shape-name');
const shapeList = document.getElementById('shape-list'); // Changed from tabsHeader
const tabsContent = document.getElementById('tabs-content');
const resultsDiv = document.getElementById('results');
// sendToServerToggle and serverMessageDiv are now per-tab

// Update slider value display
rectangleCountSlider.addEventListener('input', function() {
    rectangleCountValueSpan.textContent = this.value;
    if (activeShapeId !== null) {
        const activeShape = savedShapes.find(s => s.id === activeShapeId);
        if (activeShape) {
            activeShape.numRectangles = parseInt(this.value); // Update the number of rectangles for the active shape
            drawRiemannRectangles(activeShape.id); // Redraw with new count
            updateTabContent(activeShape.id); // Update tab content
        }
    }
});

mymap.on(L.Draw.Event.CREATED, function (event) {
    var layer = event.layer;
    drawnItems.addLayer(layer); // Add the drawn polygon to the drawnItems layer

    const newPolygonCoords = layer.getLatLngs()[0].map(function(latlng) {
        return [latlng.lat, latlng.lng];
    });

    const shapeId = Date.now(); // Simple unique ID
    const shapeName = shapeNameInput.value.trim() || `Shape ${savedShapes.length + 1}`;
    const numRectangles = parseInt(rectangleCountSlider.value);

    const newShape = {
        id: shapeId,
        name: shapeName,
        polygonCoords: newPolygonCoords,
        numRectangles: numRectangles,
        drawnPolygonLayer: layer, // Store the actual Leaflet layer for the polygon
        riemannRectanglesLayer: new L.FeatureGroup(), // New feature group for its rectangles
        visible: true, // New property: initially visible
        sendToServer: false // New property: determines if rectangles for this shape are sent to server
    };
    mymap.addLayer(newShape.drawnPolygonLayer); // Add polygon layer to map
    mymap.addLayer(newShape.riemannRectanglesLayer); // Add Riemann layer to map

    savedShapes.push(newShape);

    console.log("Drawn Polygon Coordinates:", newPolygonCoords);
        const rectanglesData = drawRiemannRectangles(newShape.id);
        addShapeTab(newShape.id, newShape.name, newShape.numRectangles);
        activateShape(newShape.id); // Activate the newly drawn shape
        shapeNameInput.value = ''; // Clear shape name input
    });

// Function to send multiple shapes' rectangle data to the server
async function sendMultipleShapesToServer(shapesToSend) {
    if (shapesToSend.length === 0) {
        console.log("No shapes toggled for sending.");
        return;
    }

    // Clear previous messages for all shapes that are about to be sent
    shapesToSend.forEach(shape => {
        const tabContent = tabsContent.querySelector(`div[data-shape-id="${shape.id}"]`);
        if (tabContent) {
            const serverMessageDiv = tabContent.querySelector(`.server-message-per-shape`);
            if (serverMessageDiv) {
                serverMessageDiv.textContent = 'Sending data to server...';
                serverMessageDiv.style.color = 'orange';
            }
        }
    });

    try {
        const response = await fetch('/send_multiple_rectangles', { // New endpoint for multiple shapes
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ shapes: shapesToSend }), // Send an array of shape objects
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Server response for multiple shapes:', result);
            // Update messages for each shape based on server response
            shapesToSend.forEach(shape => {
                const tabContent = tabsContent.querySelector(`div[data-shape-id="${shape.id}"]`);
                if (tabContent) {
                    const serverMessageDiv = tabContent.querySelector(`.server-message-per-shape`);
                    if (serverMessageDiv) {
                        const shapeResult = result.results.find(r => r.shapeId === shape.id);
                        if (shapeResult && shapeResult.status === 'success') {
                            serverMessageDiv.textContent = `Server response: ${shapeResult.message}`;
                            serverMessageDiv.style.color = 'green';
                        } else if (shapeResult && shapeResult.status === 'error') {
                            serverMessageDiv.textContent = `Error: ${shapeResult.message}`;
                            serverMessageDiv.style.color = 'red';
                        } else {
                            serverMessageDiv.textContent = `Server response received.`;
                            serverMessageDiv.style.color = 'green';
                        }
                    }
                }
            });
        } else {
            const errorText = await response.text();
            console.error('Error sending multiple shapes data:', response.status, errorText);
            // Update messages for all shapes that were attempted to be sent
            shapesToSend.forEach(shape => {
                const tabContent = tabsContent.querySelector(`div[data-shape-id="${shape.id}"]`);
                if (tabContent) {
                    const serverMessageDiv = tabContent.querySelector(`.server-message-per-shape`);
                    if (serverMessageDiv) {
                        serverMessageDiv.textContent = `Error sending data: ${response.status} - ${errorText}`;
                        serverMessageDiv.style.color = 'red';
                    }
                }
            });
        }
    } catch (error) {
        console.error('Network error sending multiple shapes:', error);
        // Update messages for all shapes that were attempted to be sent
        shapesToSend.forEach(shape => {
            const tabContent = tabsContent.querySelector(`div[data-shape-id="${shape.id}"]`);
            if (tabContent) {
                const serverMessageDiv = tabContent.querySelector(`.server-message-per-shape`);
                if (serverMessageDiv) {
                    serverMessageDiv.textContent = `Network error: ${error.message}`;
                    serverMessageDiv.style.color = 'red';
                }
            }
        });
    }
}

// Function to draw Riemann approximation rectangles for a specific shape
// Returns the array of rectangle data
function drawRiemannRectangles(shapeId) {
    const shape = savedShapes.find(s => s.id === shapeId);
    if (!shape) return []; // Return empty array if shape not found

    shape.riemannRectanglesLayer.clearLayers(); // Clear previous rectangles for this shape

    const coords = shape.polygonCoords;
    const numRectangles = shape.numRectangles;

    if (coords.length < 3) { // A polygon needs at least 3 points
        if (shapeId === activeShapeId) { // Only update results div if this is the active shape
            resultsDiv.innerHTML = '<p>No rectangles calculated (polygon needs at least 3 points).</p>';
        }
        return []; // Return empty array
    }

    // Find bounding box of the polygon
    let minLat = Infinity, maxLat = -Infinity;
    let minLon = Infinity, maxLon = -Infinity;

    coords.forEach(p => {
        minLat = Math.min(minLat, p[0]);
        maxLat = Math.max(maxLat, p[0]);
        minLon = Math.min(minLon, p[1]);
        maxLon = Math.max(maxLon, p[1]);
    });

    const latStep = (maxLat - minLat) / numRectangles;
    let rectanglesData = [];

    for (let i = 0; i < numRectangles; i++) {
        const currentLat = minLat + i * latStep;
        const nextLat = currentLat + latStep;
        const midLat = currentLat + latStep / 2;

        let intersections = [];

        // Iterate through polygon edges to find intersections with the midLat line
        for (let j = 0; j < coords.length; j++) {
            const p1 = coords[j];
            const p2 = coords[(j + 1) % coords.length]; // Wrap around for the last segment

            const intersectionLon = getLineIntersection(p1[0], p1[1], p2[0], p2[1], midLat);
            if (intersectionLon !== null) {
                intersections.push(intersectionLon);
            }
        }

        // Filter out duplicate longitudes and sort them
        intersections = [...new Set(intersections)].sort((a, b) => a - b);

        // Find the longitude range within the polygon at midLat
        let segmentMinLon = Infinity;
        let segmentMaxLon = -Infinity;

        if (intersections.length >= 2) {
            segmentMinLon = intersections[0];
            segmentMaxLon = intersections[intersections.length - 1];
        } else if (intersections.length === 1) {
            segmentMinLon = intersections[0];
            segmentMaxLon = intersections[0];
        } else {
            continue; // No valid intersections for this strip
        }

        // Ensure the rectangle is valid (minLon <= maxLon)
        if (segmentMinLon !== Infinity && segmentMaxLon !== -Infinity && segmentMinLon <= segmentMaxLon) {
            const bounds = [[currentLat, segmentMinLon], [nextLat, segmentMaxLon]];
            L.rectangle(bounds, {color: "#0078ff", weight: 1, fillOpacity: 0.3}).addTo(shape.riemannRectanglesLayer);
            rectanglesData.push({
                lat_min: bounds[0][0].toFixed(6),
                lon_min: bounds[0][1].toFixed(6),
                lat_max: bounds[1][0].toFixed(6),
                lon_max: bounds[1][1].toFixed(6)
            });
        }
    }

    // Only update results div if this is the active shape
    if (shapeId === activeShapeId) {
        resultsDiv.innerHTML = '<h3>Calculated Rectangles:</h3>';
        const ul = document.createElement('ul');
        if (rectanglesData.length > 0) {
            rectanglesData.forEach(rect => {
                const li = document.createElement('li');
                li.textContent = `Lat: ${rect.lat_min}-${rect.lat_max}, Lon: ${rect.lon_min}-${rect.lon_max}`;
                ul.appendChild(li);
            });
            resultsDiv.appendChild(ul);
        } else {
            resultsDiv.innerHTML += '<p>No rectangles calculated.</p>';
        }
    }
    return rectanglesData; // Return the calculated rectangles data
}

// Helper function to find longitude intersection of a line segment with a horizontal line (at a given latitude)
function getLineIntersection(lat1, lon1, lat2, lon2, targetLat) {
    if ((lat1 <= targetLat && lat2 >= targetLat) || (lat1 >= targetLat && lat2 <= targetLat)) {
        if (lat1 === lat2) { // Horizontal line segment
            if (lat1 === targetLat) { // If the segment is on the target latitude line
                return (lon1 + lon2) / 2; // Return midpoint, or handle as needed
            }
            return null; // No intersection if not on the line
        }
        // Calculate longitude at targetLat using linear interpolation
        const lon = lon1 + (targetLat - lat1) * (lon2 - lon1) / (lat2 - lat1);
        return lon;
    }
    return null;
}

function addShapeTab(shapeId, shapeName, numRectangles) {
    const listItem = document.createElement('li');
    listItem.classList.add('shape-list-item');
    listItem.dataset.shapeId = shapeId;

    const visibilityIcon = document.createElement('i');
    visibilityIcon.classList.add('fas', 'fa-eye', 'visibility-icon'); // Font Awesome eye icon
    visibilityIcon.dataset.shapeId = shapeId;
    visibilityIcon.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent listItem click from firing
        const shape = savedShapes.find(s => s.id === shapeId);
        if (shape) {
            toggleShapeVisibility(shapeId, !shape.visible);
            // Update icon class based on new visibility state
            if (shape.visible) {
                visibilityIcon.classList.remove('fa-eye-slash');
                visibilityIcon.classList.add('fa-eye');
            } else {
                visibilityIcon.classList.remove('fa-eye');
                visibilityIcon.classList.add('fa-eye-slash');
            }
        }
    });

    const sendToServerIcon = document.createElement('i');
    sendToServerIcon.classList.add('fas', 'fa-cloud-upload-alt', 'send-to-server-icon'); // Font Awesome cloud upload icon
    sendToServerIcon.dataset.shapeId = shapeId;
    sendToServerIcon.style.color = 'gray'; // Default color for off state
    sendToServerIcon.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent listItem click from firing
        const shape = savedShapes.find(s => s.id === shapeId);
        if (shape) {
            shape.sendToServer = !shape.sendToServer; // Toggle the state
            if (shape.sendToServer) {
                sendToServerIcon.style.color = 'green'; // Active color
            } else {
                sendToServerIcon.style.color = 'gray'; // Inactive color
            }
            console.log(`Shape ${shape.name} sendToServer set to: ${shape.sendToServer}`);
        }
    });

    const label = document.createElement('span'); // Changed from label to span
    label.textContent = `${shapeName} (${numRectangles})`;
    label.classList.add('shape-label'); // Add a class for styling

    listItem.appendChild(visibilityIcon);
    listItem.appendChild(sendToServerIcon); // Add the new toggle next to visibility
    listItem.appendChild(label);
    listItem.addEventListener('click', () => activateShape(shapeId)); // Simplified click listener
    shapeList.appendChild(listItem);

    const tabContentDiv = document.createElement('div');
    tabContentDiv.classList.add('tab-content-item');
    tabContentDiv.dataset.shapeId = shapeId;
    tabContentDiv.innerHTML = `
        <h4>${shapeName}</h4>
        <p>Rectangles: ${numRectangles}</p>
        <div id="server-message-${shapeId}" class="server-message-per-shape"></div>
        <div class="tab-results"></div>
    `;
    tabsContent.appendChild(tabContentDiv);
}

function updateTabContent(shapeId) {
    const shape = savedShapes.find(s => s.id === shapeId);
    if (!shape) return;

    const listItem = shapeList.querySelector(`li[data-shape-id="${shapeId}"]`);
    if (listItem) {
        // Update the text content of the label, not the whole list item
        const label = listItem.querySelector('.shape-label');
        if (label) {
            label.textContent = `${shape.name} (${shape.numRectangles})`;
        }
    }

    const tabContentDiv = tabsContent.querySelector(`div[data-shape-id="${shapeId}"]`);
    if (tabContentDiv) {
        tabContentDiv.querySelector('p').textContent = `Rectangles: ${shape.numRectangles}`;
    }
}


function toggleShapeVisibility(shapeId, isVisible) {
    const shape = savedShapes.find(s => s.id === shapeId);
    if (!shape) return;

    shape.visible = isVisible; // Update visibility state

    if (isVisible) {
        mymap.addLayer(shape.drawnPolygonLayer);
        mymap.addLayer(shape.riemannRectanglesLayer);
    } else {
        mymap.removeLayer(shape.drawnPolygonLayer);
        mymap.removeLayer(shape.riemannRectanglesLayer);
    }
}

function activateShape(shapeId) {
    // Deactivate current active shape styling
    if (activeShapeId !== null) {
        const prevActiveListItem = shapeList.querySelector(`li[data-shape-id="${activeShapeId}"]`);
        if (prevActiveListItem) {
            prevActiveListItem.classList.remove('active');
        }
        const prevActiveTabContent = tabsContent.querySelector(`div[data-shape-id="${activeShapeId}"]`);
        if (prevActiveTabContent) {
            prevActiveTabContent.classList.remove('active');
        }
    }

    // Activate new shape styling and update controls
    const newActiveShape = savedShapes.find(s => s.id === shapeId);
    if (newActiveShape) {
        activeShapeId = shapeId;
        rectangleCountSlider.value = newActiveShape.numRectangles;
        rectangleCountValueSpan.textContent = newActiveShape.numRectangles;

        const newActiveListItem = shapeList.querySelector(`li[data-shape-id="${shapeId}"]`);
        if (newActiveListItem) {
            newActiveListItem.classList.add('active');
        }
        const newActiveTabContent = tabsContent.querySelector(`div[data-shape-id="${shapeId}"]`);
        if (newActiveTabContent) {
            newActiveTabContent.classList.add('active');
            // Clear previous server messages when activating a new shape
            const serverMessageDivPerShape = newActiveTabContent.querySelector(`.server-message-per-shape`);
            if (serverMessageDivPerShape) {
                serverMessageDivPerShape.textContent = '';
            }
        }

        // Update the send to server icon state
        const sendToServerIcon = newActiveListItem.querySelector('.send-to-server-icon');
        if (sendToServerIcon) {
            if (newActiveShape.sendToServer) {
                sendToServerIcon.style.color = 'green';
            } else {
                sendToServerIcon.style.color = 'gray';
            }
        }

        // Ensure the activated shape is visible and redraw its rectangles to update results div
        if (!newActiveShape.visible) {
            toggleShapeVisibility(shapeId, true);
            // Also update the icon state if it was off
            const visibilityIcon = newActiveListItem.querySelector('.visibility-icon');
            if (visibilityIcon) {
                visibilityIcon.classList.remove('fa-eye-slash');
                visibilityIcon.classList.add('fa-eye');
            }
        }
        drawRiemannRectangles(shapeId); // Redraw to update results div
    }
}

document.getElementById('process-button').addEventListener('click', function() {
    const shapesToSend = [];
    let anyShapeProcessed = false;

    savedShapes.forEach(shape => {
        // Always update numRectangles for all shapes based on current slider value if they are active
        // Or, if we want to only update the active shape's rectangle count, we keep the old logic for that.
        // For now, let's assume the slider only affects the active shape's rectangle count.
        // If the shape is the active one, update its rectangle count and redraw.
        if (shape.id === activeShapeId) {
            shape.numRectangles = parseInt(rectangleCountSlider.value);
            drawRiemannRectangles(shape.id); // Redraw and get data for active shape
            updateTabContent(shape.id); // Update tab content for active shape
        } else {
            // Ensure rectangles are drawn for all shapes that might be sent, even if not active
            drawRiemannRectangles(shape.id);
        }

        if (shape.sendToServer) {
            anyShapeProcessed = true;
            const rectanglesData = drawRiemannRectangles(shape.id); // Ensure rectangles are up-to-date
            shapesToSend.push({
                id: shape.id,
                name: shape.name,
                rectangles: rectanglesData
            });
        } else {
            // If not sending to server, clear any previous server messages for this shape
            const tabContent = tabsContent.querySelector(`div[data-shape-id="${shape.id}"]`);
            if (tabContent) {
                const serverMessageDiv = tabContent.querySelector(`.server-message-per-shape`);
                if (serverMessageDiv) {
                    serverMessageDiv.textContent = 'Rectangles not sent to server (toggle is off).';
                    serverMessageDiv.style.color = 'gray';
                }
            }
        }
    });

    if (shapesToSend.length > 0) {
        sendMultipleShapesToServer(shapesToSend);
    } else if (!anyShapeProcessed) {
        alert("No shapes toggled for sending to server. Please toggle at least one shape or draw a polygon first.");
    }
});

// Function to send a request to Realtor.ca
async function sendRealtorRequest() {
    try {
        resultsDiv.innerHTML = '<h3>Sending request to Realtor.ca via proxy...</h3>';
        const response = await fetch('/proxy_realtor_request', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json', // Still send JSON header, but body will be empty or minimal
            },
            body: JSON.stringify({}) // Send an empty JSON object or remove body if not needed
        });

        if (response.ok) {
            const result = await response.json();
            console.log('Realtor.ca API Response (via proxy):', result);
            resultsDiv.innerHTML = '<h3>Realtor.ca API Response:</h3><pre>' + JSON.stringify(result, null, 2) + '</pre>';
        } else {
            const errorText = await response.text();
            console.error('Error sending request to Realtor.ca via proxy:', response.status, errorText);
            resultsDiv.innerHTML = '<h3>Error sending request to Realtor.ca:</h3><p>Status: ' + response.status + '</p><pre>' + errorText + '</pre>';
        }
    } catch (error) {
        console.error('Network error sending request to Realtor.ca via proxy:', error);
        resultsDiv.innerHTML = '<h3>Network error:</h3><p>' + error.message + '</p>';
    }
}

// Event listener for the new button
document.getElementById('send-request-button').addEventListener('click', sendRealtorRequest);

// Visibility toggle for the entire shape list
const visibilityToggle = document.querySelector('.visibility-toggle');
const eyeOpenIcon = visibilityToggle.querySelector('.fa-eye');
const eyeSlashIcon = visibilityToggle.querySelector('.fa-eye-slash');

visibilityToggle.addEventListener('click', () => {
    const isListVisible = shapeList.style.display !== 'none';
    if (isListVisible) {
        shapeList.style.display = 'none';
        tabsContent.style.display = 'none';
        eyeOpenIcon.style.display = 'none';
        eyeSlashIcon.style.display = 'inline-block';
    } else {
        shapeList.style.display = 'block';
        tabsContent.style.display = 'block';
        eyeOpenIcon.style.display = 'inline-block';
        eyeSlashIcon.style.display = 'none';
    }
});
