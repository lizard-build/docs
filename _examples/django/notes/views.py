from django import forms
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .models import Note


class NoteForm(forms.Form):
    text = forms.CharField(max_length=200)


@require_http_methods(["GET", "POST"])
def index(request):
    form = NoteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        Note.objects.create(text=form.cleaned_data["text"])
        return redirect("/")
    return render(request, "notes/index.html", {
        "form": form,
        "notes": Note.objects.order_by("-id")[:20],
    })
