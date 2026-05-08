from .base import ProcessingTransformer
from datex2_xml2json.util import find


class RoadsRegioTransformer(ProcessingTransformer):
    def __init__(
        self, path: str = "payload/sitSituationPublication/situation/situationRecord"
    ):
        super().__init__(path)

    def process(self, situation_record_wrapper: dict):
        if (
            isinstance(situation_record_wrapper, dict)
            and len(situation_record_wrapper) == 1
        ):
            situation_record = situation_record_wrapper.get(
                next(iter(situation_record_wrapper.keys()))
            )
        else:
            situation_record = situation_record_wrapper

        locationGroup = situation_record.get("locationReference", {}).get(
            "locSingleRoadLinearLocation", {}
        )
        # BEMaS
        # Expectation:
        # locationGroup/
        #   linearExtended/gmlLineString/roadInformation
        # .  linearWithinLinearElement[0]/linearElement
        # Result:
        #  linearElement/locLinearElementByLineString/
        # .   gmlLineString/locGmlLineString
        # .   roadNumber
        # .   roadName
        linearExtended = locationGroup.pop("linearExtended", None)
        if isinstance(linearExtended, dict) and "gmlLineString" in linearExtended:
            gmlLineString = linearExtended["gmlLineString"]
            # roadInformation is not part of gmlLineString any more, remove it
            gmlLineString.pop("roadInformation", {})
            linearWithinLinearElements = locationGroup.get(
                "linearWithinLinearElement", []
            )

            # Copy roadinformation and gmlLineString to locLinearElementByLineString
            if len(linearWithinLinearElements) == 1:
                linearElement = linearWithinLinearElements[0].get("linearElement", {})
                locLinearElementByLineString = {
                    "gmlLineString": {"locGmlLineString": gmlLineString}
                }
                if "roadNumber" in linearElement:
                    locLinearElementByLineString["roadNumber"] = linearElement.pop(
                        "roadNumber", None
                    )
                if "roadName" in linearElement:
                    locLinearElementByLineString["roadName"] = linearElement.pop(
                        "roadName", None
                    )

                linearElement[
                    "locLinearElementByLineString"
                ] = locLinearElementByLineString
                linearWithinLinearElements[0]["linearElement"] = linearElement

        # Remove originalNumberOfLanes
        # TODO should they be added elsewhere
        if "impact" in situation_record:
            originalNumberOfLanes = situation_record["impact"].pop(
                "originalNumberOfLanes", None
            )

        # Remove comments without value
        if "generalPublicComment" in situation_record:
            strcomments = [
                c
                for c in situation_record["generalPublicComment"]
                if isinstance(c["comment"]["values"][0], str)
            ]
            comments = [
                c
                for c in situation_record["generalPublicComment"]
                if c["comment"]["values"][0].get("value") is not None
            ]
            situation_record["generalPublicComment"] = comments
