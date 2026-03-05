function switchFilter(id, switches) {
    //flip 
    console.log('Item ID:', id);
    let new_switches = JSON.parse(document.getElementById('my-switches').textContent);
    console.log('switches:', new_switches);
    new_switches[id] = !new_switches[id]
    console.log('new_switches:', new_switches);
    let currentUrl = window.location.href;
    let urlParts = currentUrl.split('?');
    let baseUrl = urlParts[0];
    let existingQueryParams = new URLSearchParams(urlParts[1] || '');
    //update
    existingQueryParams.set('switches', new_switches);
    let newUrl = baseUrl + '?' + existingQueryParams.toString();
    //reload
    window.location.replace(newUrl);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            let cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function reloadPageWithModifiedPost(newPostData) {
    // Create a new form element
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = window.location.href; // Target the current page

    // Add hidden input fields for the modified POST variables
    for (const key in newPostData) {
        if (newPostData.hasOwnProperty(key)) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = key;
            input.value = newPostData[key];
            form.appendChild(input);
        }
    }

    //Attach CSRF Cookie
    const csrftoken = getCookie('csrftoken');
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrftoken; // Use the retrieved token
    form.appendChild(csrfInput);

    // Append the form to the body and submit it
    document.body.appendChild(form);
    form.submit();
}

// Wait for DOM to be fully loaded, and attach remaining event listeners
document.addEventListener('DOMContentLoaded', function() {
    
    //for dynamically (no-refresh) changing images on click
    document.getElementById('collapse').addEventListener('click', function(e) {
        const tgt = e.target.closest('.images'); //TODO pick a class name for <img>s
        if (tgt) {
            console.log('Edit button clicked for post ID:', tgt.dataset.postId); //TODO finish
            // Add your logic here
        }
    });
});