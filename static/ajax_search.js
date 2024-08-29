let page = 1
let has_next = true
let loading = false
const gamesContainer = $(".game-list-container")
const gameList = $(".game-list")

function load(query) {
    if (has_next === false || loading === true) {
        return
    }
    $.ajax({
        url: "ajax_search", type: "get", //send it through get method
        data: {
            query: query, page: page
        }, beforeSend: function () {
            loading = true
            $(".loading").show();
        }, success: function (response) {
            response.items.forEach(function (item) {
                let image_id = 'default'
                if (item.image_id != null) {
                    image_id = item.image_id
                }
                gameList.append(`<li class='col-md-6'>
                                    <div class="game-card bg-info-subtle">
                                        <img src="static/covers/small_${image_id}.jpg" alt="${item.name} cover">
                                        <a style="vertical-align: middle" href="/game/${item.id}">${item.name}</a>
                                    </div>
                                </li>`)
            })
            page++;
            has_next = response.has_next
        }, complete: function () {
            loading = false
            $(".loading").hide()
            if (has_next === false) {
                $(".end-of-results").show()
            } else {
                checkContainerHeight(query)
            }
        }
    });
}

function checkContainerHeight(query) {
    if (gameList[0].scrollHeight <= gamesContainer[0].clientHeight) {
        load(query);
    }
}

function init(query, gameUrl) {
    $(document).ready(function () {
        gamesContainer.on('scroll', function () {
            if (gamesContainer[0].scrollTop + gamesContainer[0].clientHeight >= gamesContainer[0].scrollHeight) {
                load(query)
            }
        })

        load(query)
    })
}

