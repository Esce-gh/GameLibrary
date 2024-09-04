$(document).ready(function () {
    let cookie = document.cookie
    let csrfToken = cookie.substring(cookie.indexOf('=') + 1)

    $('#apply-button').click(function (e) {
        e.preventDefault();

        let formData = $('#library-entry-form').serializeArray();

        let data = {};
        formData.forEach(function (item) {
            if (['playing', 'completed', 'retired'].includes(item.name)) {
                data[item.name] = true
            } else if (data[item.name] === "") {
                data[item.name] = null
            } else if (['review'].includes(item.name)) {
                data[item.name] = item.value
            } else if (['rating', 'hours_played', 'num_completions'].includes(item.name)) {
                data[item.name] = parseFloat(item.value)
            } else {
                data[item.name] = item.value
            }
        });
        if (!validate(data)) {
            return
        }
        $.ajax({
            url: `edit`,
            type: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data),
            headers: {
                'X-CSRFToken': csrfToken
            },
            success: function (response) {
                alert("Library entry updated successfully!");
            },
            error: function (xhr, status, error) {
                alert("An error occurred: " + error);
            }
        });
    });
});

function validate(data) {
    if (data['rating'] < 1 || data['rating'] > 10) {
        alert("Rating must be between 1.0 and 10.0")
        return false
    }
    if (data['hours_played'] < 0) {
        alert("Hours played must be at least 0")
        return false
    }
    if (data['num_completions'] < 0) {
        alert("Number of completions must be at least 0!")
        return false
    }
    return true
}