import json

# Exports are like outputs but for text
# Screentop Example:
# {
#   "1": {
#     "kind": "TILE",
#     "name": "security/loot - 1",
#     "frontFillColor": "#ffffff",
#     "backFillColor": "#ffc8a1",
#     "strokeColor": "#000000",
#     "frontAsset": "security-front-security",
#     "frontAssetIndex": 1,
#     "backAsset": "security-back-loot",
#     "backAssetIndex": 1
#   },
#   "2": {
#     "kind": "TILE",
#     "name": "security/loot - 2",
#     "frontFillColor": "#ffffff",
#     "backFillColor": "#ffc8a1",
#     "strokeColor": "#000000",
#     "frontAsset": "security-front-security",
#     "frontAssetIndex": 2,
#     "backAsset": "security-back-loot",
#     "backAssetIndex": 2
#   },
#
#  Take a list of Outputs
#  Then we have a series of directives which render a set of cards (data_source, card_range, front_output, back_output)
#
#   Maybe we can do it automatically somehow?
#   Output could have a "component" field indicating which component and side it is associated with
#   When we export to a format, say screentop:
#       collect each component to create the list of outputs
#       for each candidate component:
#           unify all data sets - match up each (data source, card range, front_output, back_output)
# #             (maybe front and back are just slots, so it could support more than 2 "sides")
#               only one (data source, card range) should exist for each possible card range
#               for each card in all data sources:
                    # {"kind": "TILE",
                    # "name": f"{component_title} - {index}",
                    # "frontFillColor": f"{component_front_fill}"",
                    # "backFillColor": f"{component_back_fill}",
                    # "strokeColor": f"{component_stroke}",
                    # "frontAsset": f"{get_range_asset(data_source, index, 'front')}",
                    # "frontAssetIndex": f"{front_output.get_index(card)}",
                    # "backAsset": f"{get_range_asset(data_source, index, 'front')}",
                    # "backAssetIndex": f"{back_output.get_index(card)}"}
# Output can be defined as using the same index for all of its linked cards
# We may need to think about this a bit more

class ExportComponentSpan:
    """One range of cards to be exported as a component"""
    def __init__(self, data_source, card_range, output_map: dict):
        self.data_source = data_source
        self.card_range = card_range
        self.output_map = output_map  # front output, back output etc
class ExportComponents:
    def __init__(self, project):
        self.project = project
        self.components = {}

        for output in project.outputs.values():
            if not output.component:
                continue

            component_name = output.component["component_name"]
            if component_name in self.components:
                spans = self.components[component_name]
            else:
                self.components[component_name] = spans = []

            asset_side = output.component["asset_side"]
            data_source = project.get_data_source(output.data_source_name)
            card_range = output.get_card_range(project)

            existing = False
            for span in spans:
                if span.card_range == card_range and span.data_source == data_source:
                    span.output_map[asset_side] = output
                    existing = True

            if not existing:
                span = ExportComponentSpan(data_source, card_range, {
                    asset_side: output
                })
                spans.append(span)

        screen_top = {}
        for component_name in self.components:
            print(f"Component: {component_name}")
            card_index = 1
            spans = self.components[component_name]
            for span in spans:
                span_index = 1
                for card in span.data_source.cards:
                    d = {
                        "kind": "TILE",
                        "name": f"{component_name} - {card_index}",
                        "frontFillColor": "#ffffff",
                        "backFillColor": "#ffc8a1",
                        "strokeColor": "#000000",
                        "frontAsset": span.output_map["front"].file_name,
                        "frontAssetIndex": span_index,
                        "backAsset": span.output_map["back"].file_name,
                        "backAssetIndex": span_index
                    }
                    screen_top[str(card_index)] = d
                    card_index += 1
                    span_index += 1
        print(json.dumps(screen_top, indent=4))