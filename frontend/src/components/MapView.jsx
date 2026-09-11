import React, { useEffect, useRef } from 'react';

export default function MapView({ pickup, destination, liveLocation, height = '350px' }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current) return;
    if (typeof window.L === 'undefined') return;

    const L = window.L;

    // Normalize coordinate formats (handles both lat/lon and latitude/longitude)
    const pickupLat = pickup ? (pickup.latitude ?? pickup.lat) : null;
    const pickupLon = pickup ? (pickup.longitude ?? pickup.lon) : null;
    const destLat = destination ? (destination.latitude ?? destination.lat) : null;
    const destLon = destination ? (destination.longitude ?? destination.lon) : null;
    const liveLat = liveLocation ? (liveLocation.latitude ?? liveLocation.lat) : null;
    const liveLon = liveLocation ? (liveLocation.longitude ?? liveLocation.lon) : null;

    const centerLat = pickupLat ?? 22.5726;
    const centerLon = pickupLon ?? 88.3639;

    if (!mapInstanceRef.current) {
      const map = L.map(mapRef.current).setView([centerLat, centerLon], 12);

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(map);

      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    map.eachLayer((layer) => {
      if (layer instanceof L.Marker || layer instanceof L.Polyline) {
        map.removeLayer(layer);
      }
    });

    const bounds = [];

    // Green marker for Pickup
    if (pickupLat != null && pickupLon != null) {
      const pickupMarker = L.marker([pickupLat, pickupLon], {
        title: 'Pickup Location',
      }).addTo(map);
      pickupMarker.bindPopup(`<b>Pickup Point</b><br/>${pickup.name || 'Start Location'}`);
      bounds.push([pickupLat, pickupLon]);
    }

    // Red marker for Destination
    if (destLat != null && destLon != null) {
      const destMarker = L.marker([destLat, destLon], {
        title: 'Destination',
      }).addTo(map);
      destMarker.bindPopup(`<b>Destination</b><br/>${destination.name || 'End Location'}`);
      bounds.push([destLat, destLon]);
    }

    // Draw route line if both present
    if (pickupLat != null && pickupLon != null && destLat != null && destLon != null) {
      const polyline = L.polyline(
        [
          [pickupLat, pickupLon],
          [destLat, destLon],
        ],
        { color: '#06b6d4', weight: 4, opacity: 0.8, dashArray: '8, 8' }
      ).addTo(map);

      map.fitBounds(polyline.getBounds(), { padding: [40, 40] });
    } else if (bounds.length > 0) {
      map.fitBounds(bounds, { maxZoom: 14, padding: [30, 30] });
    }

    // Live driver position marker if tracking
    if (liveLat != null && liveLon != null) {
      const liveMarker = L.marker([liveLat, liveLon], {
        title: 'Driver Live Location',
      }).addTo(map);
      liveMarker.bindPopup('<b>🚗 Driver Live Tracking</b><br/>In Progress...');
    }
  }, [pickup, destination, liveLocation]);

  return (
    <div
      ref={mapRef}
      style={{ height, width: '100%' }}
      className="rounded-xl overflow-hidden shadow-2xl border border-slate-700/50"
    />
  );
}
