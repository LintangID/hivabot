from flask import Blueprint
from .webhooks import dp
from . import db
from .models import Rule, Gejala, Stadium, ProsesDiagnosa, RiwayatDiagnosa

diagnosa = Blueprint('diagnosa', __name__)

def pertanyaan():
    daftar_rule = {}
    daftar_gejala = []
    
    rules = Rule.query.all()
    gejala = Gejala.query.all()
    for item in gejala:
        daftar_gejala.append(item.id)

    for item in rules:
        stadium = item.stadium_id
        gejala_rule = item.gejala_id

        if stadium not in daftar_rule:
            daftar_rule[stadium] = []
        daftar_rule[stadium].append(gejala_rule)
        
    count_gejala = {gejala: sum(gejala in gejala_list for gejala_list in daftar_rule.values()) for gejala in daftar_gejala}
    gejala_terbanyak = max(count_gejala, key=count_gejala.get)
    kemunculan = count_gejala[gejala_terbanyak]
    gejala_pertanyaan = Gejala.query.filter_by(id=gejala_terbanyak).first()
    pertanyaan = f"Apakah anda {gejala_pertanyaan.gejala}"
    return {'pertanyaan':pertanyaan,
            'daftar_rule':daftar_rule,
            'daftar_gejala':daftar_gejala,
            'gejala_terbanyak':gejala_terbanyak,
            'kemunculan': kemunculan
    }

def forwardChaining(cf,data):
    kemunculan = data['kemunculan']
    daftar_stadium = data['daftar_stadium']
    daftar_gejala = data['daftar_gejala']
    gejala_terbanyak = data['gejala_terbanyak']
    daftar_stadium_copy = daftar_stadium.copy()
    if kemunculan < 4:
        if len(daftar_stadium) > 1 and cf == 0:
            for stadium, gejala_list in daftar_stadium.items():
                if gejala_terbanyak in gejala_list:
                    del daftar_stadium_copy[stadium]
        elif len(daftar_stadium) > 1 and cf != 0:
            for stadium, gejala_list in daftar_stadium.items():
                if gejala_terbanyak not in gejala_list:
                    del daftar_stadium_copy[stadium]
    elif kemunculan == 4 and cf == 0:
        if gejala_terbanyak in daftar_gejala:
            daftar_gejala.remove(gejala_terbanyak)
        count_gejala = {gejala: sum(gejala in gejala_list for gejala_list in daftar_stadium_copy.values()) for gejala in daftar_gejala}
        gejala_terbanyak_berikutnya = max(count_gejala, key=count_gejala.get)
        kemunculan_gejala_berikutnya = count_gejala[gejala_terbanyak_berikutnya]
        if kemunculan_gejala_berikutnya < 4:
            terinfeksi = ProsesDiagnosa.query.filter(ProsesDiagnosa.cf > 0).all()
            if not terinfeksi:
                for stadium, gejala_list in daftar_stadium.items():
                    if gejala_terbanyak in gejala_list:
                        del daftar_stadium_copy[stadium]
                gejala_terbanyak = 0
                return {'daftar_stadium':daftar_stadium_copy,
                        'daftar_gejala':daftar_gejala,
                        'gejala_terbanyak':gejala_terbanyak
                }
            
    if gejala_terbanyak in daftar_gejala:
        daftar_gejala.remove(gejala_terbanyak)
    count_gejala = {gejala: sum(gejala in gejala_list for gejala_list in daftar_stadium_copy.values()) for gejala in daftar_gejala}
    gejala_non_zero = dict(filter(lambda item: item[1] != 0, count_gejala.items()))

    if gejala_non_zero:
        gejala_terbanyak = max(gejala_non_zero, key=gejala_non_zero.get)
        gejala_pertanyaan = Gejala.query.filter_by(id=gejala_terbanyak).first()
        kemunculan = count_gejala[gejala_terbanyak]
        pertanyaan = f"Apakah anda {gejala_pertanyaan.gejala}"
        return {'daftar_stadium':daftar_stadium_copy,
                'daftar_gejala':daftar_gejala,
                'gejala_terbanyak':gejala_terbanyak,
                'pertanyaan':pertanyaan,
                'kemunculan': kemunculan           
        }
    else:
        gejala_terbanyak = 0
        return {'daftar_stadium':daftar_stadium_copy,
            'daftar_gejala':daftar_gejala,
            'gejala_terbanyak':gejala_terbanyak
        }

def certaintyFactor(daftar_stadium,riwayat_id):
    daftar_gejala = {}
    cf_gejala = []
    proses_diagnosa = ProsesDiagnosa.query.filter_by(riwayat_id=riwayat_id).all()
    for item in proses_diagnosa:
        gejala_id = item.gejala_id
        cf_user = item.cf

        if gejala_id not in daftar_gejala:
            daftar_gejala[gejala_id] = 0
        daftar_gejala[gejala_id] += cf_user
    id_stadium = list(daftar_stadium.keys())
    
    id_gejala = list(daftar_gejala.keys())
    for id in id_gejala:
        rule = Rule.query.filter_by(stadium_id=id_stadium[0],gejala_id=id).first()
        if rule:
            nilai_cf = rule.term.nilai_cf*float(daftar_gejala[id])
            cf_gejala.append(nilai_cf)
    for key, value in enumerate(cf_gejala):
        if key == 0:
            cf_old = value
        else:
            cf_old = cf_old + value * (1-cf_old)
            
    persentase = cf_old*100
    formatted_presentase = '{:.2f}'.format(persentase)
    
    stadium = Stadium.query.filter_by(id=id_stadium[0]).first()
    riwayat_diagnosa = RiwayatDiagnosa.query.filter_by(id=riwayat_id).first()
    riwayat_diagnosa.hasil_diagnosa = stadium.id
    riwayat_diagnosa.hasil_cf = formatted_presentase
    db.session.commit()
    hasil = f"Anda {formatted_presentase}% kemungkinan terinfeksi HIV pada {stadium.stadium}"
    return hasil