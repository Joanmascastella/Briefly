
  async function updateAccountVersion(userId, newVersion) {
    const row = document.getElementById(`user-row-${userId}`);

    try {
      const response = await fetch('/custom-admin/dashboard/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          account_version: newVersion
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Show an error message
        showMessage(errorData.error || 'Something went wrong updating version.', "danger");
        // highlight row in red
        row.classList.add('table-danger');
        setTimeout(() => row.classList.remove('table-danger'), 2500);
        return;
      }

      const data = await response.json();

      // Show success message
      showMessage(data.message || 'Account version updated!', "success");

      // highlight the row in green
      row.classList.add('table-success');
      setTimeout(() => row.classList.remove('table-success'), 1500);

    } catch (error) {
      // any network or parse error
      showMessage('Network error. Could not update account version.', "danger");
      row.classList.add('table-danger');
      setTimeout(() => row.classList.remove('table-danger'), 2500);
    }
  }