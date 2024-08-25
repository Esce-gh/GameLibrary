let page = 1
let has_next = true
let loading = false

function load(query) {
    if (has_next === false || loading === true) {
        return
    }
    $.ajax({
        url: "ajax_search",
        type: "get", //send it through get method
        data: {
            query: query,
            page: page
        },
        beforeSend: function () {
            loading = true
            $(".loading").show();
        },
        success: function (response) {
            response.items.forEach(function (item) {
                $(".game-list").append(`<div class='game-container'><a href="/game/${item.id}">${item.name}</a></div>`)
            })
            has_next = response.has_next
            page++;
        },
        complete: function () {
            loading = false
            $(".loading").hide()
        }
    });
}

function init(query, gameUrl) {
    $(document).ready(function () {
        let gamesContainer = $(".game-list-container")

        gamesContainer.on('scroll', function () {
            if (gamesContainer[0].scrollTop + gamesContainer[0].clientHeight >= gamesContainer[0].scrollHeight) {
                load(query)
            }
        })

        load(query)
    })

}

