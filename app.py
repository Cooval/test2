from flask import Flask, render_template, request, send_file, abort
from io import BytesIO
from generator import svg_bytes_from_params, external_dims
import cairosvg
import webbrowser
import threading
import time

app = Flask(__name__, static_folder="templates")

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            # pobieramy parametry z formularza
            L   = float(request.form["L"])
            B   = float(request.form["B"])
            H   = float(request.form["H"])      # H = H2
            R   = float(request.form["R"])
            ep1 = float(request.form["ep1"])    # = th1

            ext_dims = external_dims(L, B, H, ep1)
            logo = app.static_folder + "/MB-print-logo11.png"
            svg_bytes = svg_bytes_from_params(
                L,
                B,
                H,
                R,
                ep1,
                logo_path=logo,
                ext_dims=ext_dims,
            )
            pdf_bytes = cairosvg.svg2pdf(bytestring=svg_bytes)

            file_name = f"Box_{L:g}x{B:g}x{H:g}_{ep1:g}mm.pdf"

            return send_file(BytesIO(pdf_bytes),
                              download_name=file_name,
                              mimetype="application/pdf",
                              as_attachment=True)
        except (KeyError, ValueError):
            abort(400, "Niepoprawne dane wejściowe")

    return render_template("index.html")

if __name__ == "__main__":
    def open_browser():
        time.sleep(1)
        webbrowser.open_new("http://127.0.0.1:5000/")

    threading.Thread(target=open_browser).start()
    app.run()
