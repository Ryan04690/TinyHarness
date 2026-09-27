# Messages are for the model, Trace is for the Harness / developers / Evaluation.

from dataclasses import (
    asdict,
    dataclass,
    field,
)


@dataclass(frozen=True)
class TraceEvent:
    event_type: str
    step: int | None = None
    data: dict = field(default_factory=dict)

# e.g.
# TraceEvent(
#     event_type="context_estimate",
#     step=3,
#     data={
#         "messages_tokens": 3015,
#         "tools_tokens": 619,
#         "total_tokens": 3641,
#     },
# )

@dataclass
class ExecutionTrace:
    events: list[TraceEvent] = field(
        default_factory=list
    )

    def record(
        self,
        event_type: str,
        step: int | None = None,
        **data,
    ):
        event = TraceEvent(
            event_type=event_type,
            step=step,
            data=dict(data),
        )

        self.events.append(event)

        return event

    def by_type(
        self,
        event_type: str,
    ):
        return [
            event
            for event in self.events
            if event.event_type
            == event_type
        ]

    def to_dict(self):
        return {
            "events": [
                asdict(event)
                for event
                in self.events
            ]
        }

    def __len__(self):
        return len(self.events)