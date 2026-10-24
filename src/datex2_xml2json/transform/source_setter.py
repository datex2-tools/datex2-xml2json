from datex2_xml2json.transform.base import SituationRecordTransformer


class SourceSetter(SituationRecordTransformer):
    """
    This Transformer sets situationRecord/source/sourceIdentification and the
    custom extension payload/payloadPublicationExtension/publicationIdentifier,
    if they are specified in the constructor call.
    """

    sourceIdentification: str | None = None
    publicationIdentifier: str | None = None

    def __init__(self, publicationIdentifier: str | None, sourceIdentification: str | None):
        super().__init__('d2LogicalModel/payload/situation/situationRecord')
        self.publicationIdentifier = publicationIdentifier
        self.sourceIdentification = sourceIdentification

    def process_situation_record(self, situation_record: dict) -> None:
        situation_record['source'] = {'sourceIdentification': self.sourceIdentification}

    def transform(self, publication: dict) -> dict:
        if self.sourceIdentification is not None:
            publication = super().transform(publication)

        if self.publicationIdentifier is not None:
            publication['d2LogicalModel']['payload'].setdefault('payloadPublicationExtension', {})['publicationIdentifier'] = (
                self.publicationIdentifier
            )

        return publication
