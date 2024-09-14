let cookie = document.cookie
let csrfToken = cookie.substring(cookie.indexOf('=') + 1)
let disabled = false
let gameImportStatus = $('.game-import-status')
$("#import-steam-form").submit(function (e) {
    e.preventDefault()
    if (disabled) {
        return
    }
    $.ajax({
        url: "/library/import", type: "post",
        headers: {
            'X-CSRFToken': csrfToken
        },
        data: {
            url: $("#id_steam_url").val()
        }, beforeSend: function () {
            disabled = true
            gameImportStatus.empty()
            gameImportStatus.append(`<h4 id="game-import-loading">Loading...</h4>`)
        }, success: function (response) {
            if (response['error'] !== undefined) {
              gameImportStatus.append(`<h4>${response['error']}</h4>`)
            } else if (response['save_errors'].length === 0) {
                gameImportStatus.append(`<h4>All games imported successfully!</h4>`)
            } else {
                gameImportStatus.append(`<h4>Failed to import following games:</h4> 
                                                    Consider adding them manually
                                                    <ul class="save-error-list"></ul>`)
                response['save_errors'].forEach(function (item) {
                    $(".save-error-list").append(`<li>${item.name}</li>`)
                })
            }
        }, complete: function () {
            disabled = false
            $('#game-import-loading').remove()
        }
    });
})