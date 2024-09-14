from django import forms


class SteamImportForm(forms.Form):
    steam_url = forms.URLField(label='Steam profile url', required=True)
