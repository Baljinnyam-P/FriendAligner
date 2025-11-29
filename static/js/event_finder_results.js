document.addEventListener('DOMContentLoaded', function() {
    //Determine selected calendar type from URL or localStorage
    function getCalendarTypeFromUrl() {
      const params = new URLSearchParams(window.location.search);
      return params.get('type');
    }
    let type = getCalendarTypeFromUrl();
    if (type) {
      window.selectedCalendarType = type;
      localStorage.setItem('selectedCalendarType', type);
    } else if (localStorage.getItem('selectedCalendarType')) {
      window.selectedCalendarType = localStorage.getItem('selectedCalendarType');
    } else {
      window.selectedCalendarType = 'personal';
    }
  const places = window.eventFinderResults || [];

  // Use same context logic as calendarLogic.js
  function fetchUserContext() {
    const token = localStorage.getItem('jwt_token');
    let selectedCalendarType = window.selectedCalendarType || 'personal';
    if (!token) return Promise.reject('Missing token');
    return fetch(`/api/calendar/user_info?type=${selectedCalendarType}`, {
      method: 'GET',
      headers: { 'Authorization': 'Bearer ' + token }
    })
    .then(response => response.json())
    .then(data => ({
      user_id: data.user_id,
      group_id: data.group_id,
      calendar_id: data.calendar_id,
      calendar_type: data.calendar_type,
      is_organizer: data.is_organizer
    }));
  }

  //Modal to show place details
  async function showModal(place) {
    const modal = document.getElementById('placeModal');
    const content = document.getElementById('modalContent');
    let details = place;
    try {
      //Call to backend to get more details
      const res = await fetch(`/api/event_finder/place_details?place_id=${place.place_id}`);
      if (res.ok) {
        const data = await res.json();
        details = data.details;
      }
    } catch {}
    let addToCalendarHtml = '';
    const token = localStorage.getItem('jwt_token');
    let ctx = {};
    try {
      ctx = await fetchUserContext();
    } catch {}
    const group_id = ctx.group_id;
    const calendar_id = ctx.calendar_id;
    // Force calendar_type to 'group' if group_id is present and selectedCalendarType is 'group'
    let calendar_type = ctx.calendar_type || 'personal';
    if (window.selectedCalendarType === 'group' && group_id) {
      calendar_type = 'group';
    }
    const isOrganizer = ctx.is_organizer;
    if (token && (group_id || (calendar_id && calendar_type === 'personal'))) {
      addToCalendarHtml = `
        <div style='margin-top:1rem;'>
          <label for='eventDate'><strong>Add to Calendar:</strong></label><br>
          <input type='date' id='eventDate' style='margin-bottom:0.5rem;'>
          <button id='addToCalendarBtn' class='btn' style='width:100%;margin-top:0.5rem;'>Add to Calendar</button>
          <div id='addToCalendarMsg' style='margin-top:0.5rem; color:#1f5f67;'></div>
        </div>
      `;
      //For organizer, show finalize/delete buttons if in group context
      if (isOrganizer && group_id) {
        addToCalendarHtml += `
          <div style='margin-top:1rem;'>
            <button id='finalizeEventBtn' class='btn' style='width:100%;background:#1f5f67;color:#fff;'>Finalize Event</button>
            <button id='deleteEventBtn' class='btn' style='width:100%;background:#c00;color:#fff;margin-top:0.5rem;'>Delete Event</button>
            <div id='organizerMsg' style='margin-top:0.5rem; color:#1f5f67;'></div>
          </div>
        `;
      }
    } else {
      addToCalendarHtml = `<div style='margin-top:1rem; color:#c00;'>Login and select a group or personal calendar to add events.</div>`;
    }
    // Build modal content
    content.innerHTML = `
      <h3 style="color:#1f5f67; margin-top:0;">${details.name}</h3>
      <p><strong>Address:</strong> ${details.formatted_address || details.vicinity || ''}</p>
      <p><strong>Rating:</strong> <span style="color:#1f5f67;">${details.rating || 'N/A'}</span></p>
      ${details.website ? `<p><a href='${details.website}' target='_blank' style='color:#c2dfe3;'>Website</a></p>` : ''}
      ${details.formatted_phone_number ? `<p><strong>Phone:</strong> ${details.formatted_phone_number}</p>` : ''}
      ${details.opening_hours && details.opening_hours.weekday_text ? `<p><strong>Hours:</strong> ${details.opening_hours.weekday_text.join('<br>')}</p>` : ''}
      ${details.photos && details.photos.length ? `<div style='max-height:180px; overflow-y:auto; margin-bottom:8px;'><strong>Photos:</strong><br>${details.photos.slice(0,4).map(ref => `<img src='https://maps.googleapis.com/maps/api/place/photo?maxwidth=300&photoreference=${ref}&key=${window.mapsApiKey}' style='max-width:100%;margin-bottom:8px; border-radius:6px; box-shadow:0 1px 4px rgba(0,0,0,0.10);'>`).join('')}</div>` : ''}
      ${details.reviews && details.reviews.length ? `<div style='margin-top:8px;'><strong>Reviews:</strong><br>${details.reviews.slice(0,2).map(r => `<div style='margin-bottom:8px; background:#f8f9fa; border-radius:6px; padding:8px;'><strong style='color:#1f5f67;'>${r.author_name}</strong>: ${r.text}</div>`).join('')}</div>` : ''}
      ${addToCalendarHtml}
    `;
    modal.style.display = 'flex';
    if (token && (group_id || (calendar_id && calendar_type === 'personal'))) {
      setTimeout(() => {
        const btn = document.getElementById('addToCalendarBtn');
        if (btn) {
          btn.onclick = async function() {
            const date = document.getElementById('eventDate').value;
            const msg = document.getElementById('addToCalendarMsg');
            if (!date) {
              msg.textContent = 'Please select a date.';
              return;
            }
            btn.disabled = true;
            msg.textContent = 'Adding...';
            try {
              let bodyObj;
              if (calendar_type === 'personal') {
                bodyObj = { calendar_id, calendar_type: 'personal', place_id: place.place_id, date };
              } else {
                bodyObj = { group_id, calendar_id, place_id: place.place_id, date };
              }
              const res = await fetch('/api/events/create_from_place', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': 'Bearer ' + token
                },
                body: JSON.stringify(bodyObj)
              });
              if (res.ok) {
                msg.textContent = 'Event added to calendar!';
                btn.style.background = '#a3c4cb';
                btn.textContent = 'Added';
                //redirect to calendar view 
                setTimeout(() => {
                  modal.style.display = 'none';
                    window.location.href = '/main_menu';
                }, 1200);
              } else {
                const data = await res.json();
                msg.textContent = data.error || 'Failed to add event.';
                btn.disabled = false;
              }
            } catch (err) {
              msg.textContent = 'Error adding event.';
              btn.disabled = false;
            }
          };
        }
        // Organizer controls
        if (isOrganizer) {
          const finalizeBtn = document.getElementById('finalizeEventBtn');
          const deleteBtn = document.getElementById('deleteEventBtn');
          const orgMsg = document.getElementById('organizerMsg');
          if (finalizeBtn) {
            finalizeBtn.onclick = async function() {
              orgMsg.textContent = 'Finalizing...';
              try {
                const res = await fetch(`/api/events/group/${group_id}`,
                  { headers: { 'Authorization': 'Bearer ' + token } });
                if (res.ok) {
                  const events = await res.json();
                  const event = events.find(e => e.place_id === place.place_id);
                  if (event) {
                    const res2 = await fetch(`/api/events/finalize/${event.event_id}`, {
                      method: 'POST',
                      headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (res2.ok) {
                      orgMsg.textContent = 'Event finalized!';
                      setTimeout(() => { modal.style.display = 'none'; }, 1200);
                    } else {
                      orgMsg.textContent = 'Failed to finalize event.';
                    }
                  } else {
                    orgMsg.textContent = 'Event not found.';
                  }
                }
              } catch {
                orgMsg.textContent = 'Error finalizing event.';
              }
            };
          }
          if (deleteBtn) {
            deleteBtn.onclick = async function() {
              orgMsg.textContent = 'Deleting...';
              try {
                const res = await fetch(`/api/events/group/${group_id}`,
                  { headers: { 'Authorization': 'Bearer ' + token } });
                if (res.ok) {
                  const events = await res.json();
                  const event = events.find(e => e.place_id === place.place_id);
                  if (event) {
                    const res2 = await fetch(`/api/events/${event.event_id}`, {
                      method: 'DELETE',
                      headers: { 'Authorization': 'Bearer ' + token }
                    });
                    if (res2.ok) {
                      orgMsg.textContent = 'Event deleted!';
                      setTimeout(() => { modal.style.display = 'none'; }, 1200);
                    } else {
                      orgMsg.textContent = 'Failed to delete event.';
                    }
                  } else {
                    orgMsg.textContent = 'Event not found.';
                  }
                }
              } catch {
                orgMsg.textContent = 'Error deleting event.';
              }
            };
          }
        }
      }, 100);
    }
  }

  document.getElementById('modalClose').onclick = () => {
    document.getElementById('placeModal').style.display = 'none';
  };
  window.onclick = function(event) {
    const modal = document.getElementById('placeModal');
    if (event.target === modal) modal.style.display = 'none';
  };

  //Display the map location for each result
  function initMap() {
    if (!places.length) return;
    const map = new google.maps.Map(document.getElementById('map'), {
      zoom: 12,
      center: { lat: places[0].geometry.location.lat, lng: places[0].geometry.location.lng }
    });
    const infowindow = new google.maps.InfoWindow();
    places.forEach((place, idx) => {
      const marker = new google.maps.Marker({
        position: { lat: place.geometry.location.lat, lng: place.geometry.location.lng },
        map: map,
        title: place.name
      });
      marker.addListener('click', function() {
        infowindow.setContent(`<strong>${place.name}</strong><br>${place.formatted_address || place.vicinity || ''}<br>Rating: ${place.rating || 'N/A'}<br><button onclick='window.showPlaceDetails(${idx})'>More Details</button>`);
        infowindow.open(map, marker);
      });
    });
    window.showPlaceDetails = function(idx) {
      showModal(places[idx]);
    };
    document.querySelectorAll('.result-item').forEach(item => {
      item.onclick = function() {
        const idx = parseInt(item.getAttribute('data-index'));
        showModal(places[idx]);
      };
    });
  }
  window.initMap = initMap;
});
