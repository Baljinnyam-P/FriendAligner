// Fetch organizer's groups and populate dropdown
document.addEventListener('DOMContentLoaded', function() {
  const token = localStorage.getItem('jwt_token');
  const groupSelect = document.getElementById('groupSelect');
  const newGroupNameDiv = document.getElementById('newGroupNameDiv');
  const newGroupNameInput = document.getElementById('newGroupName');
  if (!token) {
    groupSelect.innerHTML = '<option value="">Login required</option>';
    groupSelect.disabled = true;
    return;
  }
  fetch('/api/group/user/organized_groups', {
    method: 'GET',
    headers: { 'Authorization': 'Bearer ' + token }
  })
  .then(response => response.json())
  .then(data => {
    const groups = data.organized_groups || [];
    groupSelect.innerHTML = '';
    if (groups.length === 0) {
      groupSelect.innerHTML = '<option value="new">Create New Group</option>';
    } else {
      groupSelect.innerHTML = '<option value="">Select a group</option>';
      groups.forEach(g => {
        groupSelect.innerHTML += `<option value="${g.group_id}">${g.group_name}</option>`;
      });
      groupSelect.innerHTML += '<option value="new">Create New Group</option>';
    }
  })
  .catch(() => {
    groupSelect.innerHTML = '<option value="">Failed to load groups</option>';
    groupSelect.disabled = true;
  });

  groupSelect.addEventListener('change', function() {
    if (groupSelect.value === 'new') {
      newGroupNameDiv.style.display = '';
    } else {
      newGroupNameDiv.style.display = 'none';
      newGroupNameInput.value = '';
    }
  });

  // Submit handler
  document.getElementById('inviteForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const emailsRaw = document.getElementById('emails').value;
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;
    const group_id = groupSelect ? groupSelect.value : '';
    const feedback = document.getElementById('feedback');
    feedback.innerHTML = '';
    if (!emailsRaw || !month || !year) {
      feedback.innerHTML = '<span style="color:red;">Please fill all fields.</span>';
      return;
    }
    const emails = emailsRaw.split(',').map(e => e.trim()).filter(e => e);
    if (emails.length === 0) {
      feedback.innerHTML = '<span style="color:red;">Enter at least one valid email.</span>';
      return;
    }
    document.getElementById('sendBtn').disabled = true;
    feedback.innerHTML = 'Sending...';
    try {
      let payload = { emails, month: parseInt(month), year: parseInt(year) };
      if (group_id && group_id !== '' && group_id !== 'new') {
        payload.group_id = group_id;
      }
      if (group_id === 'new') {
        const newGroupName = newGroupNameInput ? newGroupNameInput.value.trim() : '';
        if (!newGroupName) {
          feedback.innerHTML = '<span style="color:red;">Please enter a group name.</span>';
          document.getElementById('sendBtn').disabled = false;
          return;
        }
        payload.group_name = newGroupName;
      }
      const res = await authFetch('/api/invite/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + (localStorage.getItem('jwt_token') || '')
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (res.ok) {
        window.location.href = `/invite_confirmation?group_name=${encodeURIComponent(data.group_name)}&month=${data.month}&year=${data.year}&invited=${encodeURIComponent(data.invited.map(i=>i.email).join(','))}`;
      } else {
        feedback.innerHTML = `<span style=\"color:red;\">${data.error || 'Failed to send invites.'}</span>`;
      }
    } catch (err) {
      feedback.innerHTML = '<span style="color:red;">Error sending invites.</span>';
    }
    document.getElementById('sendBtn').disabled = false;
  });
});