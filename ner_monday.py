from flask import Flask, request, render_template, redirect, send_from_directory
import os
import pandas as pd
from PyPDF2 import PdfReader
from pdfminer.high_level import extract_text
from openai import OpenAI
import json
import datetime

app = Flask(__name__)
api_key = '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'
UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def count_pdfs(directory):
    pdf_count = sum(1 for file in os.listdir(directory) if file.lower().endswith('.pdf'))
    return pdf_count

def count_pdfs_today(directory):
    today = datetime.date.today()
    pdf_count = sum(1 for file in os.listdir(directory) if file.lower().endswith('.pdf') and
                    datetime.date.fromtimestamp(os.path.getmtime(os.path.join(directory, file))) == today)
    return pdf_count

def count_pdfs_last_three_months(directory):
    today = datetime.date.today()
    start_of_month = today.replace(day=1)
    three_months_ago = start_of_month - datetime.timedelta(days=3 * 30)
    pdf_count = sum(1 for file in os.listdir(directory) if file.lower().endswith('.pdf') and
                    three_months_ago <= datetime.date.fromtimestamp(os.path.getctime(os.path.join(directory, file))) <= today)
    return pdf_count

def extract_text_from_pdf(pdf_path, start_page, end_page):
    text = extract_text(pdf_path, page_numbers=range(start_page, end_page + 1))
    return text

template = """
# Anda Adalah Seorang Hakim Agung Di Mahkamah Agung Di Indonesia. Berdasarkan Putusan Di Bawah Ini, Berikan Kesimpulannya:
{}
Variabel Yang Harus Ada Adalah Sebagai Berikut:
- Nomor Putusan
- Tingkat Proses: [Tingkat Pertama/Tingkat Banding/Tingkat Kasasi/Peninjauan Kembali (PK)]
- Klasifikasi
- Kata Kunci
- Tanggal Register
- Hakim Ketua
- Hakim Anggota
- Panitera
- Tanggal Pendaftaran
- Lembaga Peradilan
- Nama Terdakwa
- Tempat Lahir Terdakwa
- Tanggal Lahir Terdakwa
- Usia Terdakwa
- Jenis Kelamin Terdakwa
- Kebangsaan Terdakwa
- Agama Terdakwa
- Pekerjaan Terdakwa
- Timeline
- Dakwaan: Sertakan poin-poin Jaksa Penuntut Umum (JPU) membacakan tuduhan atau dakwaan terhadap terdakwa di depan hakim.
- Pasal Dakwaan: Pasal yang didakwakan, termasuk unsur-unsur tindak pidana yang dituduhkan
- Pembelaan: Sertakan poin-poin Pengacara terdakwa memberikan pembelaan terhadap dakwaan yang disampaikan.
- Saksi dan Bukti: sebukan Saksi-saksi yang dipanggil untuk memberikan keterangan, dan uraikan bukti-bukti diperiksa oleh hakim.
- Tuntutan Jaksa: Sertakan poin-poin Setelah semua bukti diperiksa, jaksa mengajukan tuntutan atau rekomendasi hukuman kepada hakim.
- Putusan Hakim Pengadilan Negeri: Sertakan poin-poin Hakim memutuskan apakah terdakwa bersalah atau tidak, dan jika bersalah, menetapkan hukuman yang sesuai.
- Banding: Sertakan poin-poin Alasan Jika salah satu pihak tidak puas dengan putusan Pengadilan Negeri, mereka dapat mengajukan banding ke Pengadilan Tinggi.
- Putusan Hakim Pengadilan Tinggi: Pengadilan Tinggi dapat menguatkan, mengubah, atau membatalkan putusan Pengadilan Negeri berdasarkan argumen dan bukti yang ada dan uraikan alasannya.
- Kasasi: Sertakan poin-poin alasan Jika pihak yang kalah di Pengadilan Tinggi masih tidak puas, mereka dapat mengajukan kasasi ke Mahkamah Agung.
- Putusan Hakim Mahkamah Agung: Mahkamah Agung dapat menguatkan, mengubah, atau membatalkan putusan Pengadilan Tinggi. Putusan Mahkamah Agung adalah putusan final dan tidak dapat diajukan banding lagi dan uraikan alasannya.
- Tuntutan: Jelaskan tuntutan yang diajukan oleh jaksa penuntut umum, baik dari segi jenis hukuman maupun lamanya hukuman yang diminta. Contoh: "Jaksa menuntut pidana penjara selama seumur hidup."
- Putusan Pengadilan Negeri: Dalam putusan pengadilan tingkat pertama, rincikan "Pasal Dakwaan" yang diajukan oleh jaksa penuntut umum, serta "Tuntutan Pemidanaannya", Penjelasan ini harus mencakup pasal-pasal yang relevan dan hukuman yang diminta oleh jaksa. contoh format: "Terdakwa didakwa melanggar Pasal 378 KUHP tentang Penipuan, dengan tuntutan pidana penjara selama 3 tahun."
- Putusan Pengadilan Tinggi: Hasil putusan Pengadilan Tinggi harus dinyatakan dengan tegas, apakah "Memperkuat" atau "Menolak" putusan pengadilan tingkat pertama. Sertakan pula alasan singkat yang mendasari putusan tersebut.Contoh: "Pengadilan Tinggi memperkuat putusan Pengadilan Negeri dengan alasan bahwa semua unsur tindak pidana telah terbukti secara sah dan meyakinkan."
- Putusan Mahkamah Agung: Untuk putusan MA yang berakhir dengan "kabul," kaidah hukum yang menjadi dasar pertimbangan MA harus dijelaskan secara rinci. Mulailah penjelasan ini dengan: "Mahkamah Agung berpendapat..." dan lanjutkan dengan uraian mengenai prinsip hukum yang diterapkan dalam kasus tersebut
- Amar Putusan Pengadilan Negeri: 'Sertakan poin-poin dari catatan amar putusan Pengadilan Negeri'
- Amar Putusan Pengadilan Tinggi: 'Sertakan poin-poin dari catatan amar putusan Pengadilan Tinggi'
- Amar Putusan Mahkamah Agung: 'Sertakan poin-poin dari catatan amar putusan Mahkamah Agung'
- Kesimpulan: 'Nama Terdakwa, usia, dinyatakan bersalah melanggar Pasal Dakwaan berdasarkan putusan Lembaga Peradilan nomor Nomor Putusan Akhir yang terdaftar pada tanggal Tanggal Registrasi. Pengadilan memutuskan Hasil Putusan Akhir, dan menjatuhkan hukuman Hukuman.'

Keterangan:
- Urutan Tingkat Proses dari yang terendah sampai yang tertinggi Tingkat Pertama < Tingkat Banding < Tingkat Kasasi, Peninjauan Kembali (PK)
- Tingkat Kasasi dan Peninjauan Kembali (PK) memiliki tingkatan yang sama namun keduanya berbeda baik dari prosedur maupun amar putusannya

- Informasi 'Tingkat Proses' dan 'Lembaga Peradilan' selalu berkaitan dengan 'Nomor Putusan', dengan contoh sebagai berikut:
    Jika contoh 'Nomor Putusan == '158/Pid.B/2023/PN Arm' terdapat informasi 'PN' menunjukan 'Lembaga Peradilan' == Pengadilan Negeri dan 'Tingkat Proses' == 'Tingkat Pertama'
    Jika contoh 'Nomor Putusan == '31/PID.SUS/2024/PT DPS' terdapat informasi 'PT' menunjukan 'Lembaga Peradilan' == Pengadilan Tinggi dan 'Tingkat Proses' == 'Tingkat Banding'
    Jika contoh 'Nomor Putusan == '1993 K/PID.SUS/2019' terdapat informasi 'K' menunjukan 'Tingkat Proses' == 'Tingkat Banding' dan 'Lembaga Peradilan' == Mahkamah Agung
    Jika contoh 'Nomor Putusan == '156 PK/Pid.Sus/2019' terdapat informasi 'PK' menunjukan 'Tingkat Proses' == 'Peninjauan Kembali' dan 'Lembaga Peradilan' == Mahkamah Agung

Jika 'Tingkat Proses' == Tingkat Pertama:
    - 'Amar Putusan Pengadilan Negeri dicirikan dengan kalimat setelah kata "MENGADILI: ..." atau "M E N G A D I L I" tolong isikan dengan detail catatan Amar nya'

Jika 'Tingkat Proses' == 'Tingkat Banding':
    - 'Amar Putusan Pengadilan Tinggi dicirikan dengan kalimat setelah kata "MENGADILI: ..." atau "M E N G A D I L I" atau "MENGADILI SENDIRI" atau "MENGADILI KEMBALI" tolong isikan dengan detail Amar nya'
    - 'Amar Putusan Pengadilan Negeri dicirikan dengan kalimat setelah kata "Membaca Putusan Pengadilan Negeri [Nama Kota] Nomor [Nomor Putusan ...]" tolong isikan dengan detail Amar nya'

Jika 'Tingkat Proses == 'Tingkat Kasasi' dan 'Tingkat Proses == 'Peninjauan Kembali':
    - 'Amar Putusan Pengadilan Mahkamah Agung dicirikan dengan kalimat setelah kata "MENGADILI: ..." atau "M E N G A D I L I" atau "MENGADILI SENDIRI" atau "MENGADILI KEMBALI" tolong isikan dengan detail catatan Amar nya'
    - 'Amar Putusan Pengadilan Tinggi dicirikan dengan kalimat setelah kata "Membaca Putusan Pengadilan Tinggi [Nama Kota] Nomor [Nomor Putusan ...]" tolong isikan dengan detail catatan Amar nya'
    - 'Amar Putusan Pengadilan Negeri dicirikan dengan kalimat setelah kata "Membaca Putusan Pengadilan Negeri [Nama Kota] Nomor [Nomor Putusan ...]" tolong isikan dengan detail catatan Amar nya'

### Format "Kesimpulan":
- Template Format:
    ```
    Terdakwa bernama 'Nama Terdakwa', usia 'Usia Terdakwa', dinyatakan bersalah melanggar 'Pasal Dakwaan' berdasarkan putusan 'Lembaga Peradilan' nomor 'Nomor Putusan Akhir' yang terdaftar pada tanggal 'Tanggal Registrasi'. Pengadilan memutuskan 'Hasil Putusan Akhir', dan menjatuhkan hukuman 'Hukuman'.'
    ```
- Example:
    ```
    'John Doe, usia 35, dinyatakan bersalah melanggar Pasal 340 KUHP tentang Pembunuhan Berencana berdasarkan putusan Mahkamah Agung nomor 1993 K/PID.SUS/2019 yang terdaftar pada tanggal 1 Januari 2019. Pengadilan memutuskan bersalah, dan menjatuhkan hukuman pidana penjara selama 20 tahun.'
    ```

### Format "Putusan Mahkamah Agung":
- Template Format:
    ```
    'Lembaga Peradilan' berpendapat bahwa 'Hasil Putusan' ...., sesuai dengan prinsip hukum yang diterapkan ... sehingga putusan tersebut ... "
    
    ```
- Example:
    ```
    "Mahkamah Agung berpendapat bahwa pengadilan tingkat pertama telah salah menerapkan hukum, sehingga putusan tersebut dibatalkan."
    ```

### Format "Timeline":
- Template Format:
    ```
    Berikut adalah timeline 'hasil putusan' oleh 'lembaga putusan' untuk terdakwa bernama 'nama terdakwa': 
    1. Pada tanggal ...
    2. Pada tanggal ...
    3. Pada tanggal ...
    4. Pada tanggal ...
    5. Pada tanggal ...
    6. Pada tanggal ...
    
    ```
Tambahan: Jika Hasilnya ada Biaya Perkara maka TIDAK PERLU DITULISKAN
Jika ada lebih dari satu Terdakwa maka satukan saja dalam bentuk list misal 'Nama Terdakwa' : ['Nama Terdakwa 1', 'Nama Terdakwa 2']

"""


@app.route('/static/<filename>')
def static_pdf(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/', methods=['GET', 'POST'])
def manage_pdfs():
    extracted_text = None
    summary_result = None
    selected_pdf_path = None
    pdf_path = None
    conclusion = None
    pdf_count = count_pdfs(app.config['UPLOAD_FOLDER'])
    pdf_count_today = count_pdfs_today(app.config['UPLOAD_FOLDER'])
    pdf_count_last_three_months = count_pdfs_last_three_months(app.config['UPLOAD_FOLDER'])

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect('/')
        file = request.files['file']
        if file.filename == '':
            return redirect('/')
        if file and file.filename.lower().endswith('.pdf'):
            pdf_filename = file.filename
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
            file.save(pdf_path)
        return redirect('/')

    search_query = request.args.get('search_query', '').lower()
    pdf_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.lower().endswith('.pdf')]
    filtered_pdfs = [pdf for pdf in pdf_files if search_query in pdf.lower()]

    pdf_list = []
    for pdf in filtered_pdfs:
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf)
        try:
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)
            pdf_list.append({"Berkas Putusan": pdf, "Total Halaman": total_pages})
        except Exception as e:
            print(f"Error reading {pdf}: {e}")
            pdf_list.append({"Berkas Putusan": pdf, "Total Halaman": "Error"})
    

    pdf_df = pd.DataFrame(pdf_list)
    pdf_df= pdf_df.sort_values(by='Berkas Putusan')
    pdf_html_table = pdf_df.to_html(index=False, escape=False)

    search_query = request.args.get('search_query', '')
    filtered_pdfs = [pdf for pdf in pdf_files if search_query.lower() in pdf.lower()]
    selected_pdf = request.args.get('selected_pdf', '')
    embed_pdf = f'/static/{selected_pdf}'

    if filtered_pdfs:
        if selected_pdf in filtered_pdfs:
            selected_pdf = request.args.get('selected_pdf', '')
            pdf_path = os.path.join(UPLOAD_FOLDER, selected_pdf)
            pdf_reader = PdfReader(pdf_path)
            pdf_reader = PdfReader(pdf_path)
            page_count = len(pdf_reader.pages)

            # Use page_count to determine the range for extracting text
            if page_count > 5:
                extracted_text_first = extract_text_from_pdf(pdf_path, 0, 4)
                extracted_text_last = extract_text_from_pdf(pdf_path, page_count - 5, page_count - 1)
                extracted_text = extracted_text_first + "\n" + extracted_text_last
            else:
                extracted_text = extract_text_from_pdf(pdf_path, 0, page_count - 1)

            if extracted_text:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo-0125",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
                        {"role": "user", "content": template.format(extracted_text)}
                    ], 
                    temperature= 0.2
                )
                data = json.loads(response.choices[0].message.content)
                conclusion = data['Kesimpulan']
                for key in data:
                    if isinstance(data[key], list):
                        str_val = ""
                        for val in data[key]:
                            str_val = str_val + '\u2022' + ' '+ val + ' '
                        
                        data[key] = str_val

                df = pd.json_normalize(data)
                #df = df.rename(columns={'Kesimpulan': 'Summary'})
                df = df.T
                df.columns = ["Hasil Putusan"]
                df.to_json('PN.json', orient='records')
                summary_result = df.to_html(classes="dataframe", header=True, index=True)

                view_button = f'<button class="btn"  data-target="#viewModal" data-pdf="{embed_pdf}"></button>'
                summary_result += view_button

    return render_template(
        'index.html',
        pdf_table=pdf_html_table,
        search_query=search_query,
        filtered_pdfs=filtered_pdfs,
        extracted_text=extracted_text,
        selected_pdf_path=selected_pdf_path,
        embed_pdf=embed_pdf,
        pdf_path=pdf_path,
        summary_result=summary_result,
        conclusion=conclusion,
        pdf_count=pdf_count,
        pdf_count_today=pdf_count_today,
        pdf_count_last_three_months=pdf_count_last_three_months
    )

if __name__ == '__main__':
    app.run(debug=True)
