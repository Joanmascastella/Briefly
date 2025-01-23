function getChangeURL() {
    const languagePrefix = window.location.pathname.split('/')[1];
    return `/${languagePrefix}/custom-admin/dashboard/update/`;
}

async function updateAccountVersion(userId, newVersion) {
    const changeURL = getChangeURL();
    const row = document.getElementById(`user-row-${userId}`);

    try {
        const response = await fetch(changeURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify({
                user_id: userId,
                account_version: newVersion,
            }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            showMessage(errorData.error || 'Something went wrong updating version.', "danger");
            row.classList.add('table-danger');
            setTimeout(() => row.classList.remove('table-danger'), 2500);
            return;
        }

        const data = await response.json();
        showMessage(data.message || 'Account version updated!', "success");
        row.classList.add('table-success');
        setTimeout(() => row.classList.remove('table-success'), 1500);

    } catch (error) {
        showMessage('Network error. Could not update account version.', "danger");
        row.classList.add('table-danger');
        setTimeout(() => row.classList.remove('table-danger'), 2500);
    }
}