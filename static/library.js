function fetch_page(page) {
    $.ajax({
        url: "/library/search", type: "get",
        data: {
            query: query, page: page, sort: sort, order: order, min_rating: minRating, min_hours: minHours, status: status
        }, beforeSend: function () {
            list.empty()
        }, success: function (response) {
            response.items.forEach(function (item) {
                let image_id = 'default'
                if (item.game.image_id != null) {
                    image_id = item.game.image_id
                }
                list.append(`<div class="game-card bg-info-subtle mb-2">
                                <a class="d-flex align-items-center" style="text-decoration: none" href="/game/${item.game.id}">
                                    <img class="game-card-img me-3" height="120" width="90" src="/static/covers/small_${image_id}.jpg" alt="${item.game.name} cover"
                                    onerror="this.onerror=null; handleImageError(this, '${item.game.image_id}')">
                                    <h4 class="game-card-title align-middle me-0">${item.game.name}</h4>
                                </a>
                            </div>`)
            })
            currentPage = page
            numPages = response.num_pages
            updatePagination()
        }
    });
}

function handleImageError(imgElement, imageId) {
    imgElement.src = '/static/covers/small_default.jpg'; // Path to your default image

    fetch(`/fetch-cover-small/${imageId}`)
        .then(response => {
            if (response.ok) {
                // Try to reload the newly fetched image
                imgElement.src = `/static/covers/small_${imageId}.jpg`;
            }
        })
        .catch(error => console.error('Error fetching cover:', error));
}

function updatePagination() {
    let previous = ''
    let next = ''
    if (currentPage === numPages) {
        next = 'disabled'
    }
    if (currentPage === 1) {
        previous = 'disabled'
    }
    pagination.empty()
    pagination.append(`<li class="page-item"><a class="page-link" onclick="fetch_page(1)">First</a></li>
        <li class="page-item ${previous}"><a class="page-link" onclick="fetch_page(currentPage-1)">Previous</a></li>
        <li class="page-item active"><a class="page-link">${currentPage}</a></li>
        <li class="page-item ${next}"><a class="page-link" onclick="fetch_page(currentPage+1)">Next</a></li>
        <li class="page-item"><a class="page-link" onclick="fetch_page(numPages)">Last</a></li>`
    )
}

$(".apply-filters-button")[0].addEventListener("click", function () {
    sort = $("#sort").val()
    if (orderIcon.hasClass("bi-arrow-up")) {
        order = 1
    } else {
        order = 0
    }
    minRating = $("#min-rating")[0].value
    minHours = $("#min-hours")[0].value
    status = $("#status")[0].value
    fetch_page(currentPage)
})

$(".order-button")[0].addEventListener("click", function () {
    if (orderIcon.hasClass("bi-arrow-up")) {
        orderIcon.attr("class", "bi bi-arrow-down")
    } else {
        orderIcon.attr("class", "bi bi-arrow-up")
    }
})

const orderIcon = $("#order-button-icon")
const list = $(".library-list")
const searchText = $(".search-text")[0]
const pagination = $(".pagination")
let query = ''
let numPages = 1
let currentPage = 1
let sort = ''
let order = 0
let minRating = null
let minHours = null
let status = ''
$(".search-button")[0].addEventListener("click", function () {
    if (searchText.value !== query) {
        query = searchText.value
    }
    fetch_page(1)
})

fetch_page(1)