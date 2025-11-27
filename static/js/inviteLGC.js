 //logic to handle user input
  document.getElementById('inviteForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const emailsRaw = document.getElementById('emails').value;
    const month = document.getElementById('month').value;
    const year = document.getElementById('year').value;
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
      const res = await authFetch('/api/invite/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ emails, month: parseInt(month), year: parseInt(year) })
      });
      const data = await res.json();
      if (res.ok) {
        window.location.href = `/invite_confirmation?group_name=${encodeURIComponent(data.group_name)}&month=${data.month}&year=${data.year}&invited=${encodeURIComponent(data.invited.map(i=>i.email).join(','))}`;
      } else {
        feedback.innerHTML = `<span style="color:red;">${data.error || 'Failed to send invites.'}</span>`;
      }
    } catch (err) {
      feedback.innerHTML = '<span style="color:red;">Error sending invites.</span>';
    }
    document.getElementById('sendBtn').disabled = false;
  });