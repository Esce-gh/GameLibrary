function fetch(query, page = 1, sort, order = 0) {
    $.ajax({
        url: "/library/search", type: "get",
        data: {
            query: query, page: page, sort: sort, order: order
        }, beforeSend: function () {
            list.empty()
        }, success: function (response) {
            response.items.forEach(function (item) {
                list.append(`<li>${item.game.name}</li>`)
            })
            currentPage = page
            numPages = response.num_pages
            updatePagination()
        }
    });
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
    pagination.append(`<li class="page-item"><a class="page-link" onclick="fetch(query, 1, sort, order)">First</a></li>
        <li class="page-item ${previous}"><a class="page-link" onclick="fetch(query, currentPage-1, sort, order)">Previous</a></li>
        <li class="page-item active"><a class="page-link">${currentPage}</a></li>
        <li class="page-item ${next}"><a class="page-link" onclick="fetch(query, currentPage+1, sort, order)">Next</a></li>
        <li class="page-item"><a class="page-link" onclick="fetch(query, numPages, sort, order)">Last</a></li>`
    )
}

$(".apply-filters-button")[0].addEventListener("click", function() {
    sort = $("#sort").val()
    if (orderIcon.hasClass("bi-arrow-up")) {
        order = 1
    } else {
        order = 0
    }
    fetch(query, 1, sort, order)
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
$(".search-button")[0].addEventListener("click", function () {
    if (searchText.value !== query) {
        query = searchText.value()
    }
    fetch(query)
})

fetch(query, currentPage, sort, order)