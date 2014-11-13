import tempfile
import tarfile
import os

from yaml import safe_dump_all, safe_dump

from ooni.pipeline import settings
from ooni.pipeline.report import Report
from ooni.pipeline.utils import generate_filename


def delete_existing_report_entries(report_header):
    existing_report = settings.db.reports.find_one({
        "start_time": report_header['start_time'],
        "probe_asn": report_header['probe_asn'],
        "probe_cc": report_header['probe_cc'],
        "test_name": report_header['test_name'],
    })
    if existing_report:
        settings.db.measurements.remove({
            "report_id": existing_report["_id"]
        })
        settings.db.reports.remove({
            "_id": existing_report["_id"]
        })


def main(archive_file):
    archive_tar = tarfile.open(archive_file)
    for element in archive_tar:
        f = archive_tar.extractfile(element)
        fp, report_file = tempfile.mkstemp()
        while True:
            data = f.read()
            if not data:
                break
            os.write(fp, data)
        f.close()

        report = Report(report_file, action="sanitise")
        report_filename = generate_filename(report.header)
        report_filename_sanitised = os.path.join(
            settings.sanitised_directory,
            report_filename
        )
        report.header['report_file'] = report_filename

        report_file_sanitised = open(report_filename_sanitised, "w")

        safe_dump(report.header, report_file_sanitised, explicit_start=True,
                  explicit_end=True)
        safe_dump_all(report, report_file_sanitised, explicit_start=True,
                      explicit_end=True, default_flow_style=False)
        delete_existing_report_entries(report.header)

        report_file_sanitised.close()
        os.remove(report_file)
