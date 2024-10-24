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
# Anda Adalah Seorang Hakim Agung Di Mahkamah Agung Di Indonesia. Berdasarkan Putusan Di Bawah Ini:
{}
Variabel Yang Harus Ada Adalah Sebagai Berikut:
- Nomor Putusan:
- Tingkat Proses : [Tingkat Pertama/Tingkat Banding/Tingkat Kasasi/Peninjauan Kembali (PK)]
- Nama Pengadilan Tinggi: 
- Nama Pengadilan Negeri: 
- Nama Pengadilan Terakhir: 
- Tanggal Sidang:
- Tempat Sidang: 
- Terdakwa: 
- Jaksa Penuntut Umum: 
- Penasehat Hukum: 
- Hakim yang Mengadili:
- Hakim Ketua: 
- Hakim Anggota: 
- Hakim Ad Hoc (jika ada): 
- Nama Terdakwa:
- Tempat Lahir Terdakwa:
- Tanggal Lahir Terdakwa:
- Usia Terdakwa:
- Jenis Kelamin Terdakwa:
- Kebangsaan Terdakwa:
- Agama Terdakwa:
- Pekerjaan Terdakwa:
- Pasal Dakwaan:
- Dakwaan : Uraikan secara detail pasal-pasal yang didakwakan kepada terdakwa, termasuk unsur-unsur tindak pidana yang dituduhkan. Contoh: "Terdakwa didakwa melanggar Pasal 340 KUHP tentang Pembunuhan Berencana.
- Tuntutan: Jelaskan tuntutan yang diajukan oleh jaksa penuntut umum, baik dari segi jenis hukuman maupun lamanya hukuman yang diminta. Contoh: "Jaksa menuntut pidana penjara selama seumur hidup.
- Pelanggaran Dakwaan:
- Pengajuan Kasasi Oleh: 
- Alasan Pengajuan Kasasi: 
- Jenis Perkara:
- Masalah Hukum Spesifik: 
- Ringkasan Kasus: Gambaran singkat mengenai kasus, termasuk peristiwa utama yang menyebabkan persidangan.
- Kronologi Kejadian: Rincian urutan kejadian terkait perkara, tanggal, pasal, waktu mulai dari insiden awal hingga sidang terakhir.
- Faktor yang memberatkan: 
- Faktor yang meringankan:
- Barang Bukti: Daftar terperinci dari semua barang yang diajukan sebagai bukti, beserta deskripsinya.
- Dokumen Terkait: Dokumen tambahan atau referensi hukum lainnya yang menjadi bagian dari berkas perkara.
- Nomor putusan Pengadilan Negeri:
- Nama Hakim Putusan Pengadilan Negeri:
- Hasil putusan Pengadilan Negeri:
- Jenis Hukuman Putusan Pengadilan Negeri:
- Pasal-Pasal yang Dilanggar Putusan Pengadilan Negeri:
- Penjelasan Singkat putusan Pengadilan Negeri:
- Tanggal putusan Pengadilan Negeri:
- Fakta yang Terbukti Putusan Pengadilan Negeri:
- Analisis Hukum Putusan Pengadilan Negeri:
- Faktor yang Memberatkan Putusan Pengadilan Negeri:Faktor-faktor yang menyebabkan hukuman menjadi lebih berat, seperti tingkat keparahan kejahatan atau catatan pelanggaran sebelumnya.
- Faktor yang Meringankan Putusan Pengadilan Negeri:Keadaan yang dapat menyebabkan hukuman menjadi lebih ringan, seperti penyesalan terdakwa atau kerjasama dengan pihak berwenang.
- Nomor putusan Pengadilan Tinggi:
- Nama Hakim Putusan Pengadilan Tinggi:
- Hasil putusan Pengadilan Tinggi:
- Jenis Hukuman Putusan Pengadilan Tinggi:
- Pasal-Pasal yang Dilanggar Putusan Pengadilan Tinggi:
- Penjelasan Singkat putusan Pengadilan Tinggi:
- Tanggal putusan Pengadilan Tinggi:
- Fakta yang Terbukti Putusan Pengadilan Tinggi:
- Analisis Hukum Putusan Pengadilan Tinggi:
- Faktor yang Memberatkan Putusan Pengadilan Tinggi:Faktor-faktor yang menyebabkan hukuman menjadi lebih berat, seperti tingkat keparahan kejahatan atau catatan pelanggaran sebelumnya.
- Faktor yang Meringankan Putusan Pengadilan Tinggi:Keadaan yang dapat menyebabkan hukuman menjadi lebih ringan, seperti penyesalan terdakwa atau kerjasama dengan pihak berwenang.
- Nomor putusan Mahkamah Agung:
- Nama Hakim Putusan Mahkamah Agung:
- Hasil putusan Mahkamah Agung:
- Jenis Hukuman Putusan Mahkamah Agung:
- Pasal-Pasal yang Dilanggar Putusan Mahkamah Agung:
- Penjelasan Singkat putusan Mahkamah Agung:
- Tanggal putusan Mahkamah Agung:
- Fakta yang Terbukti Putusan Mahkamah Agung:
- Analisis Hukum Putusan Mahkamah Agung:
- Faktor yang Memberatkan Putusan Mahkamah Agung:Faktor-faktor yang menyebabkan hukuman menjadi lebih berat, seperti tingkat keparahan kejahatan atau catatan pelanggaran sebelumnya.
- Faktor yang Meringankan Putusan Mahkamah Agung:Keadaan yang dapat menyebabkan hukuman menjadi lebih ringan, seperti penyesalan terdakwa atau kerjasama dengan pihak berwenang.
- Penerapan Hukum: Penjelasan tentang bagaimana hukum yang relevan diterapkan pada fakta-fakta yang terbukti dalam kasus ini.
- Pasal-Pasal yang Dilanggar: Pasal-pasal hukum yang ditemukan telah dilanggar.
- Interpretasi dan Penafsiran Hukum: Penjelasan mengenai interpretasi hukum oleh pengadilan dan alasan di balik penerapannya.
- Pertimbangan dari Putusan Sebelumnya: Referensi terhadap preseden atau putusan sebelumnya yang dipertimbangkan dalam membuat keputusan.
- Pertimbangan terhadap Argumentasi Kasasi: Pembahasan mengenai validitas argumen yang diajukan dalam kasasi dan bagaimana hal itu ditangani.
- Amar Putusan Pengadilan Negeri: Sertakan poin-poin dari catatan amarnya
- Amar Putusan Pengadilan Tinggi: Sertakan poin-poin dari catatan amarnya
- Amar Putusan Mahkamah Agung: Sertakan poin-poin dari catatan amarnya
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
    Terdakwa bernama 'Nama Terdakwa' berusia 'Usia Terdakwa', dituntut oleh Jaksa dengan pidana penjara selama 'Tuntutan Jaksa' dan dijatuhi hukuman oleh hakim berupa pidana penjara selama 'Hukuman Hakim' dan denda sebanyak 'Denda'. Faktor-faktor yang memberatkan terdakwa adalah 'Faktor yang Memberatkan', sementara faktor-faktor yang meringankan terdakwa adalah 'Faktor yang Meringankan'. Hasil ini didasarkan pada putusan 'Lembaga Peradilan' dengan nomor 'Nomor Putusan', yaitu putusan Pengadilan Negeri memvonis terdakwa selama 'Lama Hukuman Pengadilan Negeri', kemudian dilakukan banding di Pengadilan Tinggi sehingga pidana penjara menjadi 'Lama Hukuman Pengadilan Tinggi', dan dikabulkan oleh Mahkamah Agung dengan hukuman 'Hukuman Mahkamah Agung'.
    ```
- Example:
    ```
    'Terdakwa bernama John Doe berusia 35 tahun, dituntut oleh Jaksa dengan pidana penjara selama 10 tahun, dijatuhi hukuman oleh hakim berupa pidana penjara selama 8 tahun dan denda sebanyak 9 miliar. Faktor-faktor yang memberatkan terdakwa adalah Terdakwa terlibat dalam penempatan yang merugikan korban, sementara faktor-faktor yang meringankan terdakwa adalah Terdakwa tidak terlibat langsung dalam kejahatan tersebut. Hasil ini didasarkan pada putusan Pengadilan Tinggi DKI Jakarta dengan nomor 102/PID.SUS/2024/PT, yaitu putusan Pengadilan Negeri memvonis terdakwa selama 5 tahun, kemudian dilakukan banding di Pengadilan Tinggi sehingga pidana penjara menjadi 3 tahun, dan banding dikabulkan oleh Mahkamah Agung dengan hukuman denda sebesar 1 miliar dan 15 tahun penjara. '
    ```
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

     
                df.to_csv('data/data.csv')
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