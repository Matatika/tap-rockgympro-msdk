from singer_sdk.pagination import BasePageNumberPaginator
from typing_extensions import override

class RockGymProPaginator(BasePageNumberPaginator):

    @override
    def __init__(self) -> None:
        super().__init__(1)
    
    @override
    def has_more(self, response):
        paging = response.json().get("rgpApiPaging", {})
        current_page = int(paging.get("pageCurrent", 0))
        total_pages = int(paging.get("pageTotal", 0))
        return current_page < total_pages
